# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo import api, models, fields
from odoo.exceptions import UserError


class WizardAccountTaxLocal(models.TransientModel):
    _name = 'wizard.account.tax.local'

    line_id = fields.Many2one('account.move.line', string='Línea')
    name = fields.Char("Linea")
    parent_state = fields.Char("Estado")
    tax_local_ids = fields.Many2many('account.tax.local', string='Impuestos locales', required=True, readonly=True)

    def guardar_impuesto_local(self):
        self.line_id.actualiza_impuestos_locales(self.tax_local_ids)

