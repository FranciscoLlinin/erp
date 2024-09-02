from odoo import models, fields, api

class AccountTaxLocal(models.Model):
    _name = 'account.tax.local'

    #account.move.line donde se encuentra aplicado el impuesto local
    line_id = fields.Many2one('account.move.line', string='Línea')
    # account.move.line donde se guarda en bd el impuesto local
    line_tax_id = fields.Many2one('account.move.line', string='Línea')
    tax_id = fields.Many2one('account.tax', string='Impuesto')
    amount = fields.Float(string='Importe')

    def write(self, values):
        if 'amount' in values:
            balance_multiplicator = 1 if self.tax_id.amount_type == 'transferred' else -1
            actual_amount = self.amount * balance_multiplicator
            super(AccountTaxLocal, self).write(values)
            aml = self.line_tax_id
            amount = values['amount'] * balance_multiplicator
            aml.with_context(check_move_validity=False).write({
                'price_unit': amount
            })
            journal_move = self.env['account.move.line'].search([('move_id', '=', aml.move_id.id),('name', '=', False)])
            journal_amount = journal_move.price_unit - amount + actual_amount
            # self.env['account.move.line'].write([aml, move])
            journal_move.with_context(check_move_validity=False).write({
                'price_unit': journal_amount
            })
            move_id = aml.move_id
            move_id_amount_tax = move_id.amount_tax + amount - actual_amount
            move_id_amount_tax_signed = move_id.amount_tax_signed + amount - actual_amount
            move_id.write({
                'amount_tax': move_id_amount_tax,
                'amount_tax_signed': move_id_amount_tax_signed,
            })
        else:
            super(AccountTaxLocal, self).write(values)


    #TODO:
    # Revisar cuando se busca el journal está siempre buscando name en false, ver si no puede llegar también como VTA/XXXX/XXXXX