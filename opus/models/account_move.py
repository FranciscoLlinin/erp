# -*- coding: utf-8 -*-
from odoo import models, fields


class AccountMove(models.Model):
    _inherit = "account.move"

    opus_project_name = fields.Char(string='OPUS project')
    opus_estimate_code = fields.Char(string='OPUS estimate code')
    opus_document = fields.Char(string='OPUS document')
    opus_payment_type = fields.Char(string='OPUS payment type')
