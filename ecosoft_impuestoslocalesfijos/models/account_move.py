from datetime import timedelta

from odoo import api, models, fields, _
from odoo.exceptions import UserError
from odoo.tools.float_utils import float_round
from odoo.tools import float_compare, date_utils, email_split, email_re, html_escape, is_html_empty

class AccountMove(models.Model):
    _inherit = "account.move"

    def copy(self, default=None):
        default = dict(default or {})
        if (fields.Date.to_date(default.get('date')) or self.date) <= self.company_id._get_user_fiscal_lock_date():
            default['date'] = self.company_id._get_user_fiscal_lock_date() + timedelta(days=1)
        if self.move_type == 'entry':
            default['partner_id'] = False
        if not self.journal_id.active:
            default['journal_id'] = self.with_context(
                default_company_id=self.company_id.id,
                default_move_type=self.move_type,
            )._get_default_journal().id
        copied_am = super().copy(default)
        copied_am._message_log(body=_(
            'This entry has been duplicated from <a href=# data-oe-model=account.move data-oe-id=%(id)d>%(title)s</a>',
            id=self.id, title=html_escape(self.display_name)
        ))

        if copied_am.is_invoice(include_receipts=True):
            # Make sure to recompute payment terms. This could be necessary if the date is different for example.
            # Also, this is necessary when creating a credit note because the current invoice is copied.
            copied_am._recompute_payment_terms_lines()

        for line in copied_am.line_ids:
             for tli in line.tax_local_ids:
                line_name = tli.line_id.name
                line_tax_name = tli.line_tax_id.name
                line_id = next(x for x in copied_am.line_ids if x.name == line_name)
                line_tax_id = next(x for x in copied_am.line_ids if x.name == line_tax_name)
                new = {
                     'line_id': line_id.id,
                     'line_tax_id': line_tax_id.id,
                     'tax_id': tli.tax_id.id,
                     'amount': tli.amount
                }

                t = self.env['account.tax.local'].create(new)
                line.write({'tax_local_ids': [(4, t.id)]})
                line.write({'tax_local_ids': [(3, tli.id)]})

        return copied_am

    def _prepare_tax_lines_data_for_totals_from_invoice(self, tax_line_id_filter=None, tax_ids_filter=None):
        """ Prepares data to be passed as tax_lines_data parameter of _get_tax_totals() from an invoice.

            NOTE: tax_line_id_filter and tax_ids_filter are used in l10n_latam to restrict the taxes with consider
                  in the totals.

            :param tax_line_id_filter: a function(aml, tax) returning true if tax should be considered on tax move line aml.
            :param tax_ids_filter: a function(aml, taxes) returning true if taxes should be considered on base move line aml.

            :return: A list of dict in the format described in _get_tax_totals's tax_lines_data's docstring.
        """
        self.ensure_one()

        tax_line_id_filter = tax_line_id_filter or (lambda aml, tax: True)
        tax_ids_filter = tax_ids_filter or (lambda aml, tax: True)

        balance_multiplicator = -1 if self.is_inbound() else 1
        tax_lines_data = []

        for line in self.line_ids:
            tax_amount = line.amount_currency # * balance_multiplicator
            if line.tax_line_id and tax_line_id_filter(line, line.tax_line_id):

                if line.tax_line_id.amount_type == 'transferred' or  line.tax_line_id.amount_type == 'withhold':
                    tli = next((x for x in line.tax_local_ids if x.tax_id == line.tax_line_id), None)
                    bal = -1 if line.tax_line_id.amount_type == 'transferred' else 1
                    if tli:
                        tax_amount = tli.amount * bal
                    else:
                        tli = self.env['account.tax.local'].search([('line_tax_id', '=', line._origin.id),
                                                                    ('tax_id', '=', line.tax_line_id.id)])
                        if tli:
                            tax_amount = sum(t.amount * bal for t in tli)

                tax_lines_data.append({
                    'line_key': 'tax_line_%s' % line.id,
                    # 'tax_amount': line.amount_currency * balance_multiplicator,-
                    'tax_amount': tax_amount * balance_multiplicator,
                    'tax': line.tax_line_id,
                })

            if line.tax_ids:
                for base_tax in line.tax_ids.flatten_taxes_hierarchy():
                    if tax_ids_filter(line, base_tax):
                        tax_amount = self._get_tax_amount(line, base_tax)
                        tax_lines_data.append({
                            'line_key': 'base_line_%s' % line.id,
                            'base_amount': tax_amount * balance_multiplicator, # line.amount_currency * balance_multiplicator,
                            'tax': base_tax,
                            'tax_affecting_base': line.tax_line_id,
                        })

        return tax_lines_data

    def _get_tax_amount(self, line, tax):
        tax_amount = line.amount_currency
        if tax.amount_type == 'transferred' or tax.amount_type == 'withhold':
            tli = next((x for x in line.tax_local_ids if x.tax_id == line.tax_line_id), None)
            bal = -1 if tax.amount_type == 'transferred' else 1
            if tli:
                tax_amount = tli.amount * bal
            else:
                tli = self.env['account.tax.local'].search([('line_id', '=', line._origin.id),
                                                            ('tax_id', '=', tax._origin.id)])
                if tli:
                    tax_amount = tli.amount * bal
        return tax_amount

    def _recompute_tax_lines(self, recompute_tax_base_amount=False):
        """ Compute the dynamic tax lines of the journal entry.

        :param recompute_tax_base_amount: Flag forcing only the recomputation of the `tax_base_amount` field.
        """
        self.ensure_one()
        in_draft_mode = self != self._origin

        def _serialize_tax_grouping_key(grouping_dict):
            ''' Serialize the dictionary values to be used in the taxes_map.
            :param grouping_dict: The values returned by '_get_tax_grouping_key_from_tax_line' or '_get_tax_grouping_key_from_base_line'.
            :return: A string representing the values.
            '''
            return '-'.join(str(v) for v in grouping_dict.values())

        def _compute_base_line_taxes(base_line):
            ''' Compute taxes amounts both in company currency / foreign currency as the ratio between
            amount_currency & balance could not be the same as the expected currency rate.
            The 'amount_currency' value will be set on compute_all(...)['taxes'] in multi-currency.
            :param base_line:   The account.move.line owning the taxes.
            :return:            The result of the compute_all method.
            '''
            move = base_line.move_id

            if move.is_invoice(include_receipts=True):
                handle_price_include = True
                sign = -1 if move.is_inbound() else 1
                quantity = base_line.quantity
                is_refund = move.move_type in ('out_refund', 'in_refund')
                price_unit_wo_discount = sign * base_line.price_unit * (1 - (base_line.discount / 100.0))
            else:
                handle_price_include = False
                quantity = 1.0
                tax_type = base_line.tax_ids[0].type_tax_use if base_line.tax_ids else None
                is_refund = (tax_type == 'sale' and base_line.debit) or (tax_type == 'purchase' and base_line.credit)
                price_unit_wo_discount = base_line.amount_currency

            return base_line.tax_ids._origin.with_context(force_sign=move._get_tax_force_sign()).compute_all(
                price_unit_wo_discount,
                currency=base_line.currency_id,
                quantity=quantity,
                product=base_line.product_id,
                partner=base_line.partner_id,
                is_refund=is_refund,
                handle_price_include=handle_price_include,
                include_caba_tags=move.always_tax_exigible,
                line=base_line
            )

        taxes_map = {}

        # ==== Add tax lines ====
        to_remove = self.env['account.move.line']
        for line in self.line_ids.filtered('tax_repartition_line_id'):
            grouping_dict = self._get_tax_grouping_key_from_tax_line(line)
            grouping_key = _serialize_tax_grouping_key(grouping_dict)
            if grouping_key in taxes_map:
                # A line with the same key does already exist, we only need one
                # to modify it; we have to drop this one.
                to_remove += line
            else:
                taxes_map[grouping_key] = {
                    'tax_line': line,
                    'amount': 0.0,
                    'tax_base_amount': 0.0,
                    'grouping_dict': False,
                }
        if not recompute_tax_base_amount:
            self.line_ids -= to_remove

        # ==== Mount base lines ====
        for line in self.line_ids.filtered(lambda line: not line.tax_repartition_line_id):
            # Don't call compute_all if there is no tax.
            if not line.tax_ids:
                if not recompute_tax_base_amount:
                    line.tax_tag_ids = [(5, 0, 0)]
                continue

            compute_all_vals = _compute_base_line_taxes(line)

            # Assign tags on base line
            if not recompute_tax_base_amount:
                line.tax_tag_ids = compute_all_vals['base_tags'] or [(5, 0, 0)]

            for tax_vals in compute_all_vals['taxes']:
                grouping_dict = self._get_tax_grouping_key_from_base_line(line, tax_vals)
                grouping_key = _serialize_tax_grouping_key(grouping_dict)

                tax_repartition_line = self.env['account.tax.repartition.line'].browse(tax_vals['tax_repartition_line_id'])
                tax = tax_repartition_line.invoice_tax_id or tax_repartition_line.refund_tax_id

                taxes_map_entry = taxes_map.setdefault(grouping_key, {
                    'tax_line': None,
                    'amount': 0.0,
                    'tax_base_amount': 0.0,
                    'grouping_dict': False,
                })
                taxes_map_entry['amount'] += tax_vals['amount']
                taxes_map_entry['tax_base_amount'] += self._get_base_amount_to_display(tax_vals['base'], tax_repartition_line, tax_vals['group'])
                taxes_map_entry['grouping_dict'] = grouping_dict

        # ==== Pre-process taxes_map ====
        taxes_map = self._preprocess_taxes_map(taxes_map)

        # ==== Process taxes_map ====
        for taxes_map_entry in taxes_map.values():
            # The tax line is no longer used in any base lines, drop it.
            if taxes_map_entry['tax_line'] and not taxes_map_entry['grouping_dict']:
                if not recompute_tax_base_amount:
                    self.line_ids -= taxes_map_entry['tax_line']
                continue

            currency = self.env['res.currency'].browse(taxes_map_entry['grouping_dict']['currency_id'])

            # tax_base_amount field is expressed using the company currency.
            tax_base_amount = currency._convert(taxes_map_entry['tax_base_amount'], self.company_currency_id, self.company_id, self.date or fields.Date.context_today(self))

            # Recompute only the tax_base_amount.
            if recompute_tax_base_amount:
                if taxes_map_entry['tax_line']:
                    taxes_map_entry['tax_line'].tax_base_amount = tax_base_amount
                continue

            balance = currency._convert(
                taxes_map_entry['amount'],
                self.company_currency_id,
                self.company_id,
                self.date or fields.Date.context_today(self),
            )
            to_write_on_line = {
                'amount_currency': taxes_map_entry['amount'],
                'currency_id': taxes_map_entry['grouping_dict']['currency_id'],
                'debit': balance > 0.0 and balance or 0.0,
                'credit': balance < 0.0 and -balance or 0.0,
                'tax_base_amount': tax_base_amount,
            }

            if taxes_map_entry['tax_line']:
                # Update an existing tax line.
                taxes_map_entry['tax_line'].update(to_write_on_line)
            else:
                # Create a new tax line.
                create_method = in_draft_mode and self.env['account.move.line'].new or self.env['account.move.line'].create
                tax_repartition_line_id = taxes_map_entry['grouping_dict']['tax_repartition_line_id']
                tax_repartition_line = self.env['account.tax.repartition.line'].browse(tax_repartition_line_id)
                tax = tax_repartition_line.invoice_tax_id or tax_repartition_line.refund_tax_id
                taxes_map_entry['tax_line'] = create_method({
                    **to_write_on_line,
                    'name': tax.name,
                    'move_id': self.id,
                    'company_id': line.company_id.id,
                    'company_currency_id': line.company_currency_id.id,
                    'tax_base_amount': tax_base_amount,
                    'exclude_from_invoice_tab': True,
                    **taxes_map_entry['grouping_dict'],
                })

            if in_draft_mode:
                taxes_map_entry['tax_line'].update(taxes_map_entry['tax_line']._get_fields_onchange_balance(force_computation=True))

    def compute_tax_total_transferred(self):
        lines = self.line_ids
        total = super(AccountMove, self).get_total_local_transferred()
        for line in lines:
            if line.tax_line_id:
                if line.tax_line_id.amount_type == 'transferred':
                    atls = self.env['account.tax.local'].search([('line_tax_id', '=', line._origin.id),
                                                          ('tax_id', '=', line.tax_line_id.id)])
                    if atls:
                        for atl in atls:
                            total += round(atl.amount, 2)
        return total

    def get_total_local_transferred(self) -> object:
        total = 0
        for line in self.invoice_line_ids:
            taxes = line.mapped('tax_ids').filtered(
                lambda r: r.invoice_repartition_line_ids.filtered(
                    lambda rep: rep.tag_ids and rep.tag_ids[0].name.lower() == 'local') and r.amount > 0)
            total += sum(abs(t.amount / 100) * abs(line.amount_currency) for t in taxes)
        return total

    def compute_tax_total_withhold(self):
        lines = self.line_ids
        total = super(AccountMove, self).get_total_local_withhold()
        for line in lines:
            if line.tax_line_id:
                if line.tax_line_id.amount_type == 'withhold':
                    atls = self.env['account.tax.local'].search([('line_tax_id', '=', line._origin.id),
                                                          ('tax_id', '=', line.tax_line_id.id)])
                    if atls:
                        for atl in atls:
                            total += round(atl.amount, 2)
        return total

    def compute_tax_amount_v(self, tax):
        if tax.amount_type == 'transferred' or tax.amount_type == 'withhold':
            r = 0
            lines = self.line_ids.filtered(lambda l: l.tax_line_id == tax)
            for line in lines:
                atls = self.env['account.tax.local'].search([('line_tax_id', '=', line._origin.id),
                                                      ('tax_id', '=', tax.id)])
                if atls:
                    for atl in atls:
                        r += round(atl.amount, 2)
            return r
        else:
            return round(super(AccountMove, self).get_tax_amount(tax), 2)

class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    # tax_local_ids = fields.One2many('account.tax.local', 'line_id', string='Impuestos locales', ondelete='cascade')
    tax_local_ids = fields.Many2many('account.tax.local', string='Impuestos locales', ondelete='cascade')

    def onchange_tax_ids(self):
        tlis = []
        for tax in self.tax_ids:
            if tax.amount_type == 'transferred' or tax.amount_type == 'withhold':
                tli = next((x for x in self.tax_local_ids if x.line_id == self and x.tax_id == tax), None)
                if not tli:
                    tli = {
                        'line_id': self.id,
                        'tax_id': tax.id    ,
                        'amount': 0
                    }
                    tli = self.env['account.tax.local'].create(tli)
                tlis.append(tli)
        self.tax_local_ids = tlis

    def update_tax_local(self):
        tlis=[]
        for tax in self.tax_ids:
            if tax.amount_type == 'transferred' or tax.amount_type == 'withhold':
                tli = next((x for x in self.tax_local_ids if x.line_id == self and x.tax_id == tax), None)
                if not tli:
                    line_tax_id = self.env['account.move.line'].search([('move_id', '=', self.move_id.id),
                                                                        ('tax_line_id', '=', tax.id)])
                    tli = {
                        'line_id': self.id,
                        'line_tax_id': line_tax_id.id,
                        'tax_id': tax.id,
                        'amount': 0
                    }
                    tli = self.env['account.tax.local'].create(tli)
                    self.write({'tax_local_ids': [(4, tli.id)]})
                    tlis.append(tli)

    def unlink(self):
        for aml in self:
            atls = self.env['account.tax.local'].search(['|', ('line_id', '=', aml._origin.id),
                                                        ('line_tax_id', '=', aml._origin.id)])
            for atl in atls:
                atl.unlink()
        super(AccountMoveLine, self).unlink()

    def impuestos_locales(self):
        self.update_tax_local()
        wiz = self.env['wizard.account.tax.local'].create({
                                                           'name': self.name,
                                                            'line_id': self.id,
                                                           'tax_local_ids': self.tax_local_ids,
                                                            'parent_state': self.parent_state
                                                           })

        return {
            'name': 'Impuestos locales',
            'type': 'ir.actions.act_window',
            'res_model': 'wizard.account.tax.local',
            'view_mode': 'form',
            'target': 'new',
            'res_id': wiz.id,
        }

    @api.model
    def _get_price_total_and_subtotal_model(self, price_unit, quantity, discount, currency, product, partner, taxes,
                                            move_type):
        ''' This method is used to compute 'price_total' & 'price_subtotal'.

        :param price_unit:  The current price unit.
        :param quantity:    The current quantity.
        :param discount:    The current discount.
        :param currency:    The line's currency.
        :param product:     The line's product.
        :param partner:     The line's partner.
        :param taxes:       The applied taxes.
        :param move_type:   The type of the move.
        :return:            A dictionary containing 'price_subtotal' & 'price_total'.
        '''
        res = {}

        # Compute 'price_subtotal'.
        line_discount_price_unit = price_unit * (1 - (discount / 100.0))
        subtotal = quantity * line_discount_price_unit

        # Compute 'price_total'.
        # Llamo al método con la línea
        if taxes:
            taxes_res = taxes._origin.with_context(force_sign=1).compute_all(line_discount_price_unit,
                                                                             quantity=quantity, currency=currency,
                                                                             product=product, partner=partner,
                                                                             is_refund=move_type in (
                                                                                 'out_refund', 'in_refund'),
                                                                             line=self)
            res['price_subtotal'] = taxes_res['total_excluded']
            res['price_total'] = taxes_res['total_included']
        else:
            res['price_total'] = res['price_subtotal'] = subtotal
        # In case of multi currency, round before it's use for computing debit credit
        if currency:
            res = {k: currency.round(v) for k, v in res.items()}
        return res

    @api.model
    def _get_fields_onchange_balance_model(self, quantity, discount, amount_currency, move_type, currency, taxes,
                                           price_subtotal, force_computation=False):
        ''' This method is used to recompute the values of 'quantity', 'discount', 'price_unit' due to a change made
        in some accounting fields such as 'balance'.

        This method is a bit complex as we need to handle some special cases.
        For example, setting a positive balance with a 100% discount.

        :param quantity:        The current quantity.
        :param discount:        The current discount.
        :param amount_currency: The new balance in line's currency.
        :param move_type:       The type of the move.
        :param currency:        The currency.
        :param taxes:           The applied taxes.
        :param price_subtotal:  The price_subtotal.
        :return:                A dictionary containing 'quantity', 'discount', 'price_unit'.
        '''
        if move_type in self.move_id.get_outbound_types():
            sign = 1
        elif move_type in self.move_id.get_inbound_types():
            sign = -1
        else:
            sign = 1
        amount_currency *= sign

        # Avoid rounding issue when dealing with price included taxes. For example, when the price_unit is 2300.0 and
        # a 5.5% price included tax is applied on it, a balance of 2300.0 / 1.055 = 2180.094 ~ 2180.09 is computed.
        # However, when triggering the inverse, 2180.09 + (2180.09 * 0.055) = 2180.09 + 119.90 = 2299.99 is computed.
        # To avoid that, set the price_subtotal at the balance if the difference between them looks like a rounding
        # issue.
        if not force_computation and currency.is_zero(amount_currency - price_subtotal):
            return {}

        taxes = taxes.flatten_taxes_hierarchy()
        if taxes and any(tax.price_include for tax in taxes):
            # Inverse taxes. E.g:
            #
            # Price Unit    | Taxes         | Originator Tax    |Price Subtotal     | Price Total
            # -----------------------------------------------------------------------------------
            # 110           | 10% incl, 5%  |                   | 100               | 115
            # 10            |               | 10% incl          | 10                | 10
            # 5             |               | 5%                | 5                 | 5
            #
            # When setting the balance to -200, the expected result is:
            #
            # Price Unit    | Taxes         | Originator Tax    |Price Subtotal     | Price Total
            # -----------------------------------------------------------------------------------
            # 220           | 10% incl, 5%  |                   | 200               | 230
            # 20            |               | 10% incl          | 20                | 20
            # 10            |               | 5%                | 10                | 10
            force_sign = -1 if move_type in ('out_invoice', 'in_refund', 'out_receipt') else 1
            taxes_res = taxes._origin.with_context(force_sign=force_sign).compute_all(amount_currency,
                                                                                      currency=currency,
                                                                                      handle_price_include=False,
                                                                                      line=self)
            for tax_res in taxes_res['taxes']:
                tax = self.env['account.tax'].browse(tax_res['id'])
                if tax.price_include:
                    amount_currency += tax_res['amount']

        discount_factor = 1 - (discount / 100.0)
        if amount_currency and discount_factor:
            # discount != 100%
            vals = {
                'quantity': quantity or 1.0,
                'price_unit': amount_currency / discount_factor / (quantity or 1.0),
            }
        elif amount_currency and not discount_factor:
            # discount == 100%
            vals = {
                'quantity': quantity or 1.0,
                'discount': 0.0,
                'price_unit': amount_currency / (quantity or 1.0),
            }
        elif not discount_factor:
            # balance of line is 0, but discount  == 100% so we display the normal unit_price
            vals = {}
        else:
            # balance is 0, so unit price is 0 as well
            vals = {'price_unit': 0.0}
        return vals


    def actualiza_impuestos_locales(self, tax_local_ids):
        for tax_local in tax_local_ids:
            tli = next((x for x in self.tax_local_ids if x.line_id == self and x.tax_id == tax_local.tax_id), None)
            amount = round(tax_local.amount, 2)
            tli.write({
                'amount':  amount
            })

