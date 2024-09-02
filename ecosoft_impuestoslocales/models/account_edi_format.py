from lxml import etree

from odoo import models, fields
from math import copysign
from datetime import datetime



class AccountEdiFormat(models.Model):
    _inherit = 'account.edi.format'

    def _l10n_mx_edi_export_invoice_cfdi(self, invoice):
        res = super(AccountEdiFormat, self)._l10n_mx_edi_export_invoice_cfdi(invoice)
        cfdi_str = res.get('cfdi_str')

        if not cfdi_str:
            return res
        # cfdi = self.l10n_mx_edi_get_xml_etree(cfdi)
        cfdi = etree.fromstring(cfdi_str)
        if 'implocal' not in cfdi.nsmap:
            return res
        cfdi.attrib['{http://www.w3.org/2001/XMLSchema-instance}schemaLocation'] = '%s %s %s' % (
            cfdi.get('{http://www.w3.org/2001/XMLSchema-instance}schemaLocation'),
            'http://www.sat.gob.mx/implocal',
            'http://www.sat.gob.mx/sitio_internet/cfd/implocal/implocal.xsd')
        res['cfdi_str'] = etree.tostring(cfdi, pretty_print=True, xml_declaration=True, encoding='UTF-8')
        return res

    def _l10n_mx_edi_get_invoice_cfdi_values(self, invoice):
        ''' Doesn't check if the config is correct so you need to call _l10n_mx_edi_check_config first.

        :param invoice:
        :return:
        '''
        cfdi_date = datetime.combine(
            fields.Datetime.from_string(invoice.invoice_date),
            invoice.l10n_mx_edi_post_time.time(),
        ).strftime('%Y-%m-%dT%H:%M:%S')

        cfdi_values = {
            **invoice._prepare_edi_vals_to_export(),
            **self._l10n_mx_edi_get_common_cfdi_values(invoice),
            'document_type': 'I' if invoice.move_type == 'out_invoice' else 'E',
            'currency_name': invoice.currency_id.name,
            'payment_method_code': (invoice.l10n_mx_edi_payment_method_id.code or '').replace('NA', '99'),
            'payment_policy': invoice.l10n_mx_edi_payment_policy,
            'cfdi_date': cfdi_date,
        }

        # ==== Invoice Values ====
        if invoice.currency_id.name == 'MXN':
            cfdi_values['currency_conversion_rate'] = None
        else:  # assumes that invoice.company_id.country_id.code == 'MX', as checked in '_is_required_for_invoice'
            cfdi_values['currency_conversion_rate'] = abs(invoice.amount_total_signed) / abs(invoice.amount_total)

        if invoice.partner_bank_id:
            digits = [s for s in invoice.partner_bank_id.acc_number if s.isdigit()]
            acc_4number = ''.join(digits)[-4:]
            cfdi_values['account_4num'] = acc_4number if len(acc_4number) == 4 else None
        else:
            cfdi_values['account_4num'] = None

        if cfdi_values['customer'].country_id.l10n_mx_edi_code != 'MEX' and cfdi_values['customer_rfc'] not in (
        'XEXX010101000', 'XAXX010101000'):
            cfdi_values['customer_fiscal_residence'] = cfdi_values['customer'].country_id.l10n_mx_edi_code
        else:
            cfdi_values['customer_fiscal_residence'] = None

        # ==== Tax details ====

        def get_tax_cfdi_name(tax_detail_vals):
            tags = set()
            for detail in tax_detail_vals['group_tax_details']:
                for tag in detail['tax_repartition_line_id'].tag_ids:
                    tags.add(tag)
            tags = list(tags)
            if len(tags) == 1:
                return {'ISR': '001', 'IVA': '002', 'IEPS': '003'}.get(tags[0].name)
            elif tax_detail_vals['tax'].l10n_mx_tax_type == 'Exento':
                return '002'
            else:
                return None

        def filter_void_tax_line(inv_line):
            return inv_line.discount != 100.0

        #Se modifican estos métodos para que no reciban los locales
        def filter_tax_transferred(tax_values):
            return tax_values['tax_id'].amount >= 0.0 and \
                   tax_values['tax_id'].invoice_repartition_line_ids.tag_ids and \
                   tax_values['tax_id'].invoice_repartition_line_ids.tag_ids[0].name.lower() != 'local'

        def filter_tax_withholding(tax_values):
            return tax_values['tax_id'].amount < 0.0 and \
                   tax_values['tax_id'].invoice_repartition_line_ids.tag_ids and \
                   tax_values['tax_id'].invoice_repartition_line_ids.tag_ids[0].name.lower() != 'local'

        compute_mode = 'tax_details' if invoice.company_id.tax_calculation_rounding_method == 'round_globally' else 'compute_all'

        tax_details_transferred = invoice._prepare_edi_tax_details(filter_to_apply=filter_tax_transferred,
                                                                   compute_mode=compute_mode,
                                                                   filter_invl_to_apply=filter_void_tax_line)
        for tax_detail_transferred in (list(tax_details_transferred['invoice_line_tax_details'].values())
                                       + [tax_details_transferred]):
            for tax_detail_vals in tax_detail_transferred['tax_details'].values():
                tax = tax_detail_vals['tax']
                if tax.l10n_mx_tax_type == 'Tasa':
                    tax_detail_vals['tax_rate_transferred'] = tax.amount / 100.0
                elif tax.l10n_mx_tax_type == 'Cuota':
                    tax_detail_vals['tax_rate_transferred'] = tax_detail_vals['tax_amount_currency'] / tax_detail_vals[
                        'base_amount_currency']
                else:
                    tax_detail_vals['tax_rate_transferred'] = None

        cfdi_values.update({
            'get_tax_cfdi_name': get_tax_cfdi_name,
            'tax_details_transferred': tax_details_transferred,
            'tax_details_withholding': invoice._prepare_edi_tax_details(filter_to_apply=filter_tax_withholding,
                                                                        compute_mode=compute_mode,
                                                                        filter_invl_to_apply=filter_void_tax_line),
        })

        cfdi_values.update({
            'has_tax_details_transferred_no_exento': any(x['tax'].l10n_mx_tax_type != 'Exento' for x in
                                                         cfdi_values['tax_details_transferred'][
                                                             'tax_details'].values()),
            'has_tax_details_withholding_no_exento': any(x['tax'].l10n_mx_tax_type != 'Exento' for x in
                                                         cfdi_values['tax_details_withholding'][
                                                             'tax_details'].values()),
        })

        if not invoice._l10n_mx_edi_is_managing_invoice_negative_lines_allowed():
            return cfdi_values

        # ==== Distribute negative lines ====

        def is_discount_line(line):
            return line.price_subtotal < 0.0

        def is_candidate(discount_line, other_line):
            discount_taxes = discount_line.tax_ids.flatten_taxes_hierarchy()
            other_line_taxes = other_line.tax_ids.flatten_taxes_hierarchy()
            return set(discount_taxes.ids) == set(other_line_taxes.ids)

        def put_discount_on(cfdi_values, discount_vals, other_line_vals):
            discount_line = discount_vals['line']
            other_line = other_line_vals['line']

            # Update price_discount.

            remaining_discount = discount_vals['price_discount'] - discount_vals['price_subtotal_before_discount']
            remaining_price_subtotal = other_line_vals['price_subtotal_before_discount'] - other_line_vals[
                'price_discount']
            discount_to_allow = min(remaining_discount, remaining_price_subtotal)

            other_line_vals['price_discount'] += discount_to_allow
            discount_vals['price_discount'] -= discount_to_allow

            # Update taxes.

            for tax_key in ('tax_details_transferred', 'tax_details_withholding'):
                discount_line_tax_details = cfdi_values[tax_key]['invoice_line_tax_details'][discount_line][
                    'tax_details']
                other_line_tax_details = cfdi_values[tax_key]['invoice_line_tax_details'][other_line]['tax_details']
                for k, tax_values in discount_line_tax_details.items():
                    if discount_line.currency_id.is_zero(tax_values['tax_amount_currency']):
                        continue

                    other_tax_values = other_line_tax_details[k]
                    tax_amount_to_allow = copysign(
                        min(abs(tax_values['tax_amount_currency']), abs(other_tax_values['tax_amount_currency'])),
                        other_tax_values['tax_amount_currency'],
                    )
                    other_tax_values['tax_amount_currency'] -= tax_amount_to_allow
                    tax_values['tax_amount_currency'] += tax_amount_to_allow
                    base_amount_to_allow = copysign(
                        min(abs(tax_values['base_amount_currency']), abs(other_tax_values['base_amount_currency'])),
                        other_tax_values['base_amount_currency'],
                    )
                    other_tax_values['base_amount_currency'] -= base_amount_to_allow
                    tax_values['base_amount_currency'] += base_amount_to_allow

            return discount_line.currency_id.is_zero(remaining_discount - discount_to_allow)

        for line_vals in cfdi_values['invoice_line_vals_list']:
            line = line_vals['line']

            if not is_discount_line(line):
                continue

            # Search for lines on which distribute the global discount.
            candidate_vals_list = [x for x in cfdi_values['invoice_line_vals_list']
                                   if not is_discount_line(x['line']) and is_candidate(line, x['line'])]

            # Put the discount on the biggest lines first.
            candidate_vals_list = sorted(candidate_vals_list, key=lambda x: x['line'].price_subtotal, reverse=True)
            for candidate_vals in candidate_vals_list:
                if put_discount_on(cfdi_values, line_vals, candidate_vals):
                    break

        # ==== Remove discount lines ====

        cfdi_values['invoice_line_vals_list'] = [x for x in cfdi_values['invoice_line_vals_list']
                                                 if not is_discount_line(x['line'])]

        # ==== Remove taxes for zero lines ====

        for line_vals in cfdi_values['invoice_line_vals_list']:
            line = line_vals['line']

            if line.currency_id.is_zero(line_vals['price_subtotal_before_discount'] - line_vals['price_discount']):
                for tax_key in ('tax_details_transferred', 'tax_details_withholding'):
                    cfdi_values[tax_key]['invoice_line_tax_details'].pop(line, None)

        # Recompute Totals since lines changed.
        cfdi_values.update({
            'total_price_subtotal_before_discount': sum(
                x['price_subtotal_before_discount'] for x in cfdi_values['invoice_line_vals_list']),
            'total_price_discount': sum(x['price_discount'] for x in cfdi_values['invoice_line_vals_list']),
        })

        return cfdi_values
