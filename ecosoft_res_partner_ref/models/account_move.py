# -*- coding: utf-8 -*-

from odoo import fields, models, api

class AccountMove(models.Model):
    _inherit = 'account.move'
        
    partner_ref = fields.Char(string='Referencia Proveedor')
        
    @api.onchange('partner_id')
    def on_change_partner_id_change_partner_ref(self):
        if self.partner_id and self.partner_id.ref:
            self.partner_ref = self.partner_id.ref
        else:
            self.partner_ref = False
            
    @api.model
    def load(self, fields, data):
        """ Overridden para permitir importar unicamente con referencia
            del proveedor (partner_ref) y en base a ese campo asingar
            partner_id.
        """
        rslt = super(AccountMove, self).load(fields, data)
        
        if 'import_file' in self.env.context and 'partner_id' not in fields and \
            'partner_ref' in fields:
            for inv in self.browse(rslt['ids']):
                if not inv.partner_id and inv.partner_ref:
                    partner_id = self.env['res.partner'].search([('ref', '=', inv.partner_ref)])
                    if partner_id:
                        inv.partner_id = partner_id.id
                        for line in inv.line_ids:
                            line.partner_id = partner_id.id
                
        return rslt