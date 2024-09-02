# -*- coding: utf-8 -*-

from odoo import fields, models

class ResPartner(models.Model):
    _inherit = 'res.partner'
      
    ref = fields.Char(string='Reference', index=True)
    
    _sql_constraints = [
        ('ref_unique', 'unique (ref)', "La Referencia de Proveedor debe de ser unica!"),
    ]
