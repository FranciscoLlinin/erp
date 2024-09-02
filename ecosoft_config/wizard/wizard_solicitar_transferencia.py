# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo import api, models, fields
from odoo.exceptions import UserError


class EcosoftSolicitarTansferencia(models.TransientModel):
    _name = 'wizard.solicitar.transferencia'
    
    picking_id = fields.Many2one('stock.picking', string='Movimiento de Stock relacionado', required=True, readonly=True)        
    location_id = fields.Many2one('stock.location', 'Ubicacion Origen')
    location_dest_id = fields.Many2one('stock.location', 'Ubicacion Destino', required=True, readonly=True)  
    picking_type_id = fields.Many2one('stock.picking.type', 'Tipo de Operacion', required=True)  
         
    def create_stock_picking(self):
        """ Crea stock.picking para surtir picking_id desde
            la ubicacion location_id indicada. 
            Despliega nuevo stock.picking form view"""
        if not self.location_id:  
            raise UserError("Es necesario indicar ubicacion origen")
            
        default = {
            'state': 'draft',
            'sale_id': False,
            'related_picking_id': self.picking_id.id,
            'location_id': self.location_id.id,
            'location_dest_id': self.location_dest_id.id,
            'picking_type_id': self.picking_type_id.id,
            'move_line_ids': [], }
                
        new_picking = self.picking_id.copy(default=default) 
        
        for line in new_picking.move_line_ids_without_package:
            line.location_id = self.location_id.id
            line.location_dest_id = self.location_dest_id.id
            line.picking_type_id = self.picking_type_id.id
            
        for line in new_picking.move_lines:
            line.location_id = self.location_id.id
            line.location_dest_id = self.location_dest_id.id
            line.picking_type_id = self.picking_type_id.id
            
        self.picking_id.related_picking_id = new_picking.id
        self.picking_id.message_post(
                    body=('Se ha creado transferencia <a href=# data-oe-model=stock.picking data-oe-id=%d>%s</a> para surtir esta solicitud de inventario.') % (
                        new_picking.id, new_picking.name))   
        view_id = self.env['ir.model.data'].get_object_reference('stock', 'view_picking_form')[1]
        
        return {
            'name': 'Transferencias',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'stock.picking'  ,
            'view_id': view_id,
            'type': 'ir.actions.act_window',
            'target':'same',
            'context':  dict(self._context or {}),
            'res_id': new_picking.id,}
