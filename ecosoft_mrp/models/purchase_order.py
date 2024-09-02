# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError


class PurchaseOrderCausaMrp(models.Model):
    _inherit = "purchase.order"

    workorder_id = fields.Many2one('mrp.workorder', string='Orden de Trabajo', copy=False)
    workorder_state = fields.Selection(related='workorder_id.state')    
        
    # ----------------------------------------------------
    # Overriding super methods para incluir validacion MRP
    # ----------------------------------------------------
    def button_done(self):
        """ Boton BLOQUEAR No se puede una vez que 
            la orden de trabajo esta en estado:
            'ready', 'progress'.
            Esta validacion es necesaria por si despliegan
            la purchase.order desde el modulo de compras
            y no desde la orden de trabajo del modulo de
            manufactura.
        """
        # No regresara si no pasa validacion
        self._check_workorder_state()
        return super(PurchaseOrderCausaMrp, self).button_done()
        
    def button_unlock(self):
        """ Boton DESBLOQUEAR No se puede una vez que 
            la orden de trabajo esta en estado:
            'ready', 'progress'.
            Esta validacion es necesaria por si despliegan
            la purchase.order desde el modulo de compras
            y no desde la orden de trabajo del modulo de
            manufactura.
        """
        # No regresara si no pasa validacion
        self._check_workorder_state()
        return super(PurchaseOrderCausaMrp, self).button_unlock()
        
    def button_draft(self):
        """ Boton DESBLOQUEAR No se puede una vez que 
            la orden de trabajo esta en estado:
            'ready', 'progress'.
            Esta validacion es necesaria por si despliegan
            la purchase.order desde el modulo de compras
            y no desde la orden de trabajo del modulo de
            manufactura.
        """
        # No regresara si no pasa validacion
        self._check_workorder_state()
        return super(PurchaseOrderCausaMrp, self).button_draft()
        
    def button_approve(self, force=False):
        """ Boton APROBAR No se puede una vez que 
            la orden de trabajo esta en estado:
            'ready', 'progress'.
            Esta validacion es necesaria por si despliegan
            la purchase.order desde el modulo de compras
            y no desde la orden de trabajo del modulo de
            manufactura.
        """
        # No regresara si no pasa validacion
        self._check_workorder_state()
        return super(PurchaseOrderCausaMrp, self).button_approve()
                
    def button_confirm(self):
        """ Boton CONFIRMAR No se puede una vez que 
            la orden de trabajo esta en estado:
            'ready', 'progress'.
            Esta validacion es necesaria por si despliegan
            la purchase.order desde el modulo de compras
            y no desde la orden de trabajo del modulo de
            manufactura.
        """
        # No regresara si no pasa validacion
        self._check_workorder_state()
        return super(PurchaseOrderCausaMrp, self).button_confirm()      
                
    def button_cancel(self):
        """ Boton CANCELAR No se puede una vez que 
            la orden de trabajo esta en estado:
            'ready', 'progress'.
            Esta validacion es necesaria por si despliegan
            la purchase.order desde el modulo de compras
            y no desde la orden de trabajo del modulo de
            manufactura.
        """
        # No regresara si no pasa validacion
        self._check_workorder_state()
        return super(PurchaseOrderCausaMrp, self).button_cancel()
                          
    def _check_workorder_state(self, allowed_states=['ready', 'progress']):
        """ Raise error si alguna de las Ordenes de 
            Trabajo relacionadas no esta en alguno
            de los allowed_states
        """
        for order in self:
            if order.workorder_id and order.workorder_id.state not in allowed_states:            
                raise UserError(('No es posible procesar la Orden %s debido a que la Orden de Trabajo relacionada esta en estado "%s"') % (order.name, order.workorder_id.state))
       