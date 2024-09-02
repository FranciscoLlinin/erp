# -*- coding:utf-8 -*-
from odoo import models, fields


class Partner(models.Model):
    _name = "res.partner"
    _inherit = "res.partner"

    opus_code = fields.Char(string='OPUS code', groups='opus.group_opus_edit_partner_opus_code')
    is_contractor = fields.Boolean(string="Is contractor")
