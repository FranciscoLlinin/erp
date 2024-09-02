# -*- coding: utf-8 -*-
from odoo import models, fields


class AccountMove(models.Model):
    _inherit = "account.move"

    analytic_account_id = fields.Many2one('account.analytic.account',
                                          related='invoice_line_ids.analytic_account_id', string='Cuenta analítica',
                                          readonly=False)

