# -*- coding: utf-8 -*-
import logging

from odoo import api, models, fields
from odoo.exceptions import UserError
from odoo.addons import decimal_precision as dp

_logger = logging.getLogger(__name__)


class PurchaseOrder(models.Model):
    _name = "purchase.order"
    _inherit = "purchase.order"

    opus_contract_code = fields.Char(string='OPUS contract')
    opus_contract_type = fields.Char(string='OPUS contract type')
    opus_project_name = fields.Char(string='OPUS project name')
    opus_state = fields.Selection([
        ('ToValidate', 'To validate'),
        ('InProgress', 'In progress'),
        ('Terminated', 'Terminated'),
        ('Cancelled', 'Cancelled')
        ], string='OPUS state', readonly=True, copy=False, default='ToValidate', required=True)

    @api.model
    def button_approve(self, force=False):
        res = super(PurchaseOrder, self).button_approve()
        if (res == True):
            for order in self:
                if order.contrato_opus != False:
                   order.write({'opus_state': "InProgress"})
        return res

    '''
    @api.model
    def button_cancel(self, *args, **kwargs):
        for order in self:
            if order.state == 'purchase' and order.contrato_opus != False:
                raise UserError('This purchase order belongs to an OPUS '\
                        'contract. To cancel it, you must cancel the contract '\
                        'in OPUS.')
        res = super(PurchaseOrder, self).button_cancel()
        if (res == None):
            return False
        else:
            return res
    '''

    @api.model
    def create(self, vals):
        _logger.debug("vals antes de super: {}".format(vals))
        return_value = super(PurchaseOrder, self).create(vals)
        _logger.debug("vals: {}".format(vals))
        req = vals.get('requisition_id', False)
        if req:
            requisition = self.env['purchase.requisition'].search([('id', '=', req)])
            if requisition:
                return_value.opus_contract_code = requisition.opus_contract_code
                return_value.opus_project_name = requisition.opus_project_name
        return return_value


class PurchaseOrderLine(models.Model):
    _name = "purchase.order.line"
    _inherit = "purchase.order.line"

    # TODO: Cambiar referencias a dp.get_precision (método obsoleto).
    product_qty_opus = fields.Float(string='Quantity Opus',
                                    digits=dp.get_precision('Product Unit of Measure'))
    price_unit_opus = fields.Float(string='Unit Price Opus',
                                   digits=dp.get_precision('Product Price'))

    @api.model
    def create(self, values):
        return_value = super(PurchaseOrderLine, self).create(values)
        requisition = return_value.order_id.requisition_id
        # _logger.debug("requisition_id: {}".format(requisition))
        if requisition:
            lines = self.env['purchase.requisition.line'].search([('requisition_id', '=', requisition.id)])
            if lines:
                # _logger.debug('ENCONTRÉ LINEAS!!!')
                for line in lines:
                    if line.product_id == return_value.product_id:
                        return_value.product_qty_opus = line.product_qty_opus
                        return_value.price_unit_opus = line.price_unit_opus
        return return_value
