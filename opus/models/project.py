# -*- coding:utf-8 -*-
from odoo import models, fields


class Project(models.Model):
    _name = "project.project"
    _inherit = "project.project"

    opus_direct_cost = fields.Monetary(string='Direct cost')
    opus_direct_cost_currency = fields.Monetary(string='Direct cost in foreign currency')
    opus_start_date = fields.Datetime(string='Start date')
    opus_end_date = fields.Datetime(string='End date')
    opus_work_duration = fields.Float(string='Duration in working days',
                                      digits=(16, 2))
