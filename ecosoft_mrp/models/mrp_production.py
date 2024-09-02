# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models
from odoo.exceptions import UserError

import logging
_logger = logging.getLogger(__name__)


class MrpProductionCausaMrp(models.Model):
    _inherit = 'mrp.production' 
           
    def _cal_price(self, consumed_moves):
        """Set a price unit on the finished move according to `consumed_moves`.
           No se invoca al super method debido a que los cambios estan en el
           'corazon' de este metodo.
           Se agrega costo subcontractor_cost al costo de produccion
           el cual se calcula con el monto antes de impuestos de la
           orden de compra.
        """
        work_center_cost = 0
        subcontractor_cost = 0
        finished_move = self.move_finished_ids.filtered(
            lambda x: x.product_id == self.product_id and x.state not in ('done', 'cancel') and x.quantity_done > 0)
        if finished_move:
            finished_move.ensure_one()
            for work_order in self.workorder_ids:
                time_lines = work_order.time_ids.filtered(lambda x: x.date_end and not x.cost_already_recorded)
                duration = sum(time_lines.mapped('duration'))
                time_lines.write({'cost_already_recorded': True})
                work_center_cost += (duration / 60.0) * work_order.workcenter_id.costs_hour
                # ############################## INICIO ##################################
                if work_order.workcenter_id.is_subcontractig:
                    subcontractor_cost += self._cal_subcontractor_cost(work_order)
                # ############################## FIN ##################################
                    
            if finished_move.product_id.cost_method in ('fifo', 'average'):
                qty_done = finished_move.product_uom._compute_quantity(
                    finished_move.quantity_done, finished_move.product_id.uom_id)
                # #################### SE AGREGA subcontractor_cost A price_unit Y value ##########################
                # finished_move.price_unit = (sum([-m.value for m in consumed_moves]) +
                #                             work_center_cost + subcontractor_cost) / qty_done
                # finished_move.value = sum([-m.value for m in consumed_moves]) + work_center_cost + subcontractor_cost 
                
                total_cost = (sum(-m.stock_valuation_layer_ids.value for m in consumed_moves.sudo()) + 
                                work_center_cost + subcontractor_cost) / qty_done
                finished_move.price_unit = total_cost                            
                # finished_move.price_unit = (sum([-m.quantity_done * m.price_unit for m in consumed_moves]) +
                #                             work_center_cost + subcontractor_cost) / qty_done
                
            # _logger.info('ecosoft_mrp calculando precio producto finished_move: value=%s price_unit=%s',
            #              (finished_move.value, finished_move.price_unit,) )
            _logger.info('ecosoft_mrp calculando precio producto finished_move: price_unit=%s',
                         finished_move.price_unit )
        return True  
        
    def _cal_subcontractor_cost(self, work_order):
        total = 0
        for purchase in work_order.purchase_ids.filtered(lambda x: x.state in ('done') ):
            total += purchase.currency_id._convert(
                purchase.amount_untaxed, work_order.production_id.company_id.currency_id,
                work_order.production_id.company_id, purchase.date_order or fields.Date.today())
        return total


class MrpWorkorderCausaMrp(models.Model):
    _inherit = 'mrp.workorder'   
    
    is_subcontractig = fields.Boolean(related='workcenter_id.is_subcontractig',store=True)
    create_order = fields.Boolean(compute='_compute_all')
    create_picking = fields.Char(compute='_compute_all')
    purchase_ids = fields.One2many('purchase.order', 'workorder_id', string='Pedidos de Compra',
                                   states={'done': [('readonly', True)], 'cancel': [('readonly', True)]})
    picking_ids = fields.One2many('stock.picking', 'workorder_id', string='Transferencias',
                                  states={'done': [('readonly', True)], 'cancel': [('readonly', True)]})
    
    @api.depends('purchase_ids', 'picking_ids')
    def _compute_all(self):
        for mrp in self:
            mrp.create_order = mrp.is_subcontractig and len(mrp.purchase_ids) <= 0
            qty = self._calculate_qty_in_transit(mrp)
            # Si aun no se crea ningun picking -> crear el primero de salida
            if len(mrp.picking_ids) < 1:
                mrp.create_picking = 'out'
            # Ya se enviaron y regresaron todas --> No mas movimientos
            elif len(mrp.picking_ids) >= 2 and qty == self.qty_production:
                mrp.create_picking = 'none'
            # Ya se enviaron todas al proveedor -> Recibire de regreso
            elif qty <= 0:
                mrp.create_picking = 'in'
            # Se envio parcialmente --> Podemos enviar mas y/o recibir de regreso
            else:
                mrp.create_picking = 'both'
          
    @api.model
    def _calculate_qty_in_transit(self, mrp, include_picking=False):
        """ Calcula las cantidades en transito entre
            fabricacion y proveedor, regresa cantidad
            en almacen virtual de produccion, esta cantidad
            sera siempre sera:
            minimo 0 --> Todo con el Proveedor
            Igual a mrp.qty_production --> Todo en la empresa
            cuando sea menor significa que la diferencia esta
            aun con el proveedor de servicio externo.
            Unicamente se computan stock.picking en estado done
            o stock.picking en include_picking.
        """
        qty = mrp.qty_production
        for picking in mrp.picking_ids.filtered(lambda x: x.state == 'done' or x.id == include_picking):
            for move in picking.move_lines:
                # Enviados al Proveedor
                if move.location_id == mrp.production_id.product_id.property_stock_production and \
                   move.location_dest_id == mrp.workcenter_id.partner_id.property_stock_supplier:
                    qty -= move.product_qty
                # Recibidos de regreso
                elif move.location_id == mrp.workcenter_id.partner_id.property_stock_supplier and \
                     move.location_dest_id == mrp.production_id.product_id.property_stock_production:
                    qty += move.product_qty
        return qty
        
    def do_finish(self):
        """ Antes terminar esta orden de trabajo verifica
            que todas las purchase.order y stock.pickings
            (si los hay) esten en estado hecho o cancelado
         """
        errors = []
        if self.is_subcontractig:
            # Checando purchase.order
            if len( self.purchase_ids) < 1:
                errors.append('Aun no se ha creado Orden de Compra para este servicio')
            else:
                order_ok = False
                for order in self.purchase_ids:
                    if order.state not in ('done', 'cancel'):
                        errors.append('La Orden de Compra %s esta en estado "%s"; cancele o procese totalmente la orden'
                                      % (order.name, order.state))
                    if order.state in ('done'):
                        order_ok = True
                if not order_ok:
                    errors.append('Aun no existe ningun Pedido de Compra confirmado')
                
            # Checando stock.picking
            qty = self._calculate_qty_in_transit(self)
            if qty < self.qty_production:
                errors.append('Pendiente de recibir %s unidades del Proveedor externo %s' %
                              (self.qty_production - qty, self.workcenter_id.partner_id.name))
                            
            for picking in self.picking_ids:
                if picking.state not in ('done', 'cancel'):
                    errors.append('El movimiento de inventario %s esta en estado "%s"; cancele o procese totalmente el movimiento' % (picking.name, picking.state))
                    
        if len(errors) == 0:
            return super(MrpWorkorderCausaMrp, self).do_finish()
        raise UserError("Surgieron errores al intentar procesar solicitud\n%s" % '\n'.join(errors))

    def button_finish(self):
        if len(self.ids) == 1:
            if self.is_subcontractig:
                # Checando purchase.order
                if len( self.purchase_ids) < 1:
                    raise UserError("Aún no se ha creado orden de compra para este servicio")
        super(MrpWorkorderCausaMrp, self).button_finish()

    # Actions
    # --------------------------------------------------

    def action_view_purchase_order(self):
        """ This function returns an action that display purchase orders related to
        manufacturing orders. 
        Si no existe ninguna la crea en estado borrador y la despliega directamente.
        """
        self.ensure_one()
        origin ='%s-%s' % (self.production_id.name, self.name)
        action = self.env.ref('ecosoft_mrp.action_mrp_purchase_order_list').read()[0]
        orders = self.mapped('purchase_ids')
        if self.state not in ('ready', 'progress'):
            action['views'] = [(self.env.ref('ecosoft_mrp.purchase_order_tree_no_create_inherit_20').id, 'tree'),
                               (self.env.ref('ecosoft_mrp.purchase_order_form_inherit_20').id, 'form')]
        elif len(orders) < 1 and self.state in ('ready', 'progress'):
            data = self._prepare_purchase_order_values(origin) 
            order = self.env['purchase.order'].create(data)
            action['views'] = [(self.env.ref('ecosoft_mrp.purchase_order_form_inherit_20').id, 'form')]
            action['res_id'] = order.id
        else:
            action['domain'] = [('id', 'in', orders.ids)]
            action['context'] = dict(self.env.context, default_origin=origin,
                                     default_partner_id=self.workcenter_id.partner_id.id,
                                     default_workorder_id=self.id, group_by=False)
       
        return action

    def action_view_stock_picking(self):
        """ This function returns an action that display pickings related to
        manufacturing orders. 
        Si no existe ninguna la crea en estado borrador y la despliega directamente.
        """
        self.ensure_one()
        origin ='%s-%s' % (self.production_id.name, self.name)
        action = self.env.ref('ecosoft_mrp.action_mrp_stock_picking_list').read()[0]
        orders = self.mapped('picking_ids')     
        mrp_picking = self.env.context.get('mrp_picking', 'none')
        default_picking_type_id = self.production_id._get_default_picking_type()
        # Ya no se pueden crear mas pickings (workorder hecha o ya se crearon
        # picking de salida y de regreso
        if self.state not in ('ready', 'progress') or mrp_picking == 'none':    
            action['views'] = [(self.env.ref('ecosoft_mrp.vpicktree_no_create_inherit_20').id, 'tree'),
                               (self.env.ref('ecosoft_mrp.view_picking_form_inherit_20').id, 'form')]
        else:   
            context = dict(self.env.context,
                           default_origin=origin,
                           default_partner_id=self.workcenter_id.partner_id.id,
                           default_product_id=self.production_id.product_id.id,
                           default_product_uom_qty=self.qty_production,
                           default_quantity_done=self.qty_production,
                           picking_types_ids=[default_picking_type_id],
                           default_workorder_id=self.id, group_by=False)
            
            context['default_picking_type_id'] = default_picking_type_id
            if mrp_picking == 'out':
                context['picking_location_ids'] = [self.production_id.product_id.property_stock_production.id] 
                context['default_location_id'] = self.production_id.product_id.property_stock_production.id
                context['location_dest_ids'] = [self.workcenter_id.partner_id.property_stock_supplier.id]  
                context['default_location_dest_id'] = self.workcenter_id.partner_id.property_stock_supplier.id  
            elif mrp_picking == 'in':
                context['picking_location_ids'] = [self.workcenter_id.partner_id.property_stock_supplier.id]  
                context['default_location_id'] = self.workcenter_id.partner_id.property_stock_supplier.id  
                context['location_dest_ids'] = [self.production_id.product_id.property_stock_production.id] 
                context['default_location_dest_id'] = self.production_id.product_id.property_stock_production.id 
            else:   # both
                context['picking_location_ids'] = [self.production_id.product_id.property_stock_production.id,
                                                   self.workcenter_id.partner_id.property_stock_supplier.id]
                context['default_location_id'] = self.production_id.product_id.property_stock_production.id
                context['location_dest_ids'] = [self.workcenter_id.partner_id.property_stock_supplier.id,
                                                self.production_id.product_id.property_stock_production.id]
                context['default_location_dest_id'] = self.workcenter_id.partner_id.property_stock_supplier.id  
            action['context'] = context
            action['domain'] = [('id', 'in', orders.ids)]
       
        return action        
        
    def _prepare_purchase_order_values(self, origin):
        res = {}
        payment_term = self.workcenter_id.partner_id.property_supplier_payment_term_id
        
        FiscalPosition = self.env['account.fiscal.position']
        fpos = FiscalPosition.get_fiscal_position(self.workcenter_id.partner_id.id)
        fpos = FiscalPosition.browse(fpos)

        res['workorder_id'] = self.id
        res['partner_id'] = self.workcenter_id.partner_id.id
        res['fiscal_position_id'] = fpos.id
        res['payment_term_id'] = payment_term.id
        res['company_id'] = self.env.user.company_id.id
        res['currency_id'] = self.env.user.company_id.currency_id.id
        res['origin'] = origin
        res['date_order'] = fields.Datetime.now()
        res['picking_type_id'] = self.env['purchase.order']._default_picking_type().id 

        # Create PO line
        order_lines = []
        # Compute name
        product_lang = self.workcenter_id.product_id.with_context({
            'lang': self.workcenter_id.partner_id.lang,
            'partner_id': self.workcenter_id.partner_id.id,
        })
        name = product_lang.display_name
        if product_lang.description_purchase:
            name += '\n' + product_lang.description_purchase

        # Compute taxes
        if fpos:
            taxes_ids = fpos.map_tax(self.workcenter_id.product_id.supplier_taxes_id.
                                     filtered(lambda tax: tax.company_id == self.env.user.company_id)).ids
        else:
            taxes_ids = self.workcenter_id.product_id.supplier_taxes_id.\
                filtered(lambda tax: tax.company_id == self.env.user.company_id).ids

        # Compute price_unit
        seller = self.workcenter_id.product_id._select_seller(
            partner_id=self.workcenter_id.partner_id,
            quantity=1,
            date=res['date_order'],
            uom_id=self.workcenter_id.product_id.uom_po_id,
            params={})
        price_unit = self.workcenter_id.product_id.uom_po_id._compute_price(seller.price,
                                                                            self.workcenter_id.product_id.uom_po_id)

        # Create PO line
        order_line_values = {
            'name': name,
            'product_id': self.workcenter_id.product_id.id,
            'product_uom': self.workcenter_id.product_id.uom_po_id.id,
            'product_qty': 1,
            'price_unit': price_unit,
            'taxes_id': [(6, 0, taxes_ids)],
            'date_planned': fields.Datetime.now(), 
        }
                
        order_lines.append((0, 0, order_line_values))        
        res['order_line'] = order_lines
        return res


class MrpWorkcenterCausaMrp(models.Model):
    _inherit = 'mrp.workcenter' 
    
    is_subcontractig = fields.Boolean(string='Servicio subcontratado', default=False,
        help='Indica si este Centro de Trabajo pertenece a un servicio subcontratado a un tercero.')
    partner_id = fields.Many2one('res.partner', string='Proveedor')
    product_id = fields.Many2one('product.product', string='Servicio', domain=[('type', '=', 'service')])
        
