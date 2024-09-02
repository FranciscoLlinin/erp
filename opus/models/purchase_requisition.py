# -*- coding: utf-8 -*-
import logging

from odoo import api, models, fields
from odoo.exceptions import UserError
from odoo.addons import decimal_precision as dp

_logger = logging.getLogger(__name__)


class PurchaseRequistion(models.Model):
    _name = "purchase.requisition"
    _inherit = "purchase.requisition"

    opus_contract_code = fields.Char(string='OPUS contract code')
    opus_project_name = fields.Char(string='OPUS project name')


class PurchaseRequisitionLine(models.Model):
    _name = 'purchase.requisition.line'
    _inherit = 'purchase.requisition.line'

    # TODO: Cambiar referencias al método dp.get_precision (obsoleto).
    product_qty_opus = fields.Float(string='Quantity OPUS',
                                    digits=dp.get_precision('Product Unit of Measure'))
    price_unit_opus = fields.Float(string='Unit Price Opus',
                                   digits=dp.get_precision('Product Price'))

    @api.model
    def _prepare_purchase_order_line(self, name, product_qty=0.0, price_unit=0.0, taxes_ids=False):
        order_line_values = super(PurchaseRequisitionLine, self)\
            ._prepare_purchase_order_line(
            name,
            product_qty,
            price_unit,
            taxes_ids)
        product_qty_opus = self.product_qty_opus
        price_unit_opus = self.price_unit_opus
        # _logger.debug("product_qty_opus: {}".format(product_qty_opus))
        # _logger.debug("price_unit_opus: {}".format(price_unit_opus))
        order_line_values['product_qty_opus'] = product_qty_opus
        order_line_values['price_unit_opus'] = price_unit_opus
        # _logger.debug("order_line_values: {}".format(order_line_values))
        return order_line_values

