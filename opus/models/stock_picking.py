# -*- coding: utf-8 -*-

from odoo import models, fields


class Picking(models.Model):
    _name = "stock.picking"
    _inherit = "stock.picking"

    sent_to_opus = fields.Boolean(string='Sent to OPUS')
    opus_code = fields.Char(string='OPUS code')
    opus_document = fields.Char(string='OPUS document')
    opus_project_name = fields.Char(string='OPUS project name')

