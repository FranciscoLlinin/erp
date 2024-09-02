# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError


class StockPickingCausaMrp(models.Model):
    _inherit = "stock.picking"

    workorder_id = fields.Many2one('mrp.workorder', string='Orden de Trabajo', copy=False)
    production_product_id = fields.Many2one('product.product', related='workorder_id.production_id.product_id')
    workorder_state = fields.Selection(related='workorder_id.state')
    
    @api.onchange('picking_type_id', 'partner_id')
    def onchange_picking_type(self):
        res = super(StockPickingCausaMrp, self)._onchange_picking_type()
        if self.workorder_id:
            self.location_id = self.env.context.get('picking_location_ids', [self.location_id])[0] 
            self.location_dest_id = self.env.context.get('location_dest_ids', [self.location_dest_id])[0]  
        return res
    
    def action_confirm(self):
        res = super(StockPickingCausaMrp, self).action_confirm()
        if self.env.context.get('from_mrp', False):
            # No regresa si hay error
            self.valida_picking_mrp()            
        return res      
      
    def button_validate(self):
        if self.env.context.get('from_mrp', False):
            # No regresa si hay error
            self.valida_picking_mrp()
        return super(StockPickingCausaMrp, self).button_validate() 
        
    def valida_picking_mrp(self):
        """ Si este stock.picking pertenece a una orden de produccion
            verfica que el producto sea el que se esta fabricando y que
            la cantidad sea menor o igual a la cantidad fabricada
        """
        self.ensure_one()
        if self.workorder_id:
            qty = self.env['mrp.workorder']._calculate_qty_in_transit(self.workorder_id, self.id)     
            # Se esta intentando enviar a al proveedor mas de la produccion
            if qty < 0:
                raise UserError(("Esta intentando enviar al proveedor mas unidades [%s] que las de la Orden de Produccion.\nLa orden de Produccion %s para el producto %s es por %s") % (qty, self.workorder_id.production_id.name,self.workorder_id.product_id.name,self.workorder_id.qty_production ))
            # Se esta intentando recibir del proveedor mas de la produccion
            elif qty > self.workorder_id.qty_production:
                raise UserError(("Esta intentando recibir del proveedor mas unidades [%s] que las de la Orden de Produccion.\nLa orden de Produccion %s para el producto %s es por %s") % (qty, self.workorder_id.production_id.name,self.workorder_id.product_id.name,self.workorder_id.qty_production ))
                
            # Verifica que sea el producto y por la cantidad en fabricacion
            for line in self.move_lines:
                if line.location_id == self.location_dest_id:
                    raise UserError("Las ubicaciones de origen y destino deben de ser diferentes")
                if line.product_id != self.production_product_id:
                    raise UserError("El producto %s no existe en la orden de produccion %s" % (line.product_id.name, self.workorder_id.production_id.name))
                line.origin = self.origin
