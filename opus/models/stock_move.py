# -+- coding: utf-8 -+-

from odoo import models, api
import logging
_logger = logging.getLogger(__name__)


class StockMove(models.Model):
    _name = "stock.move"
    _inherit = "stock.move"

    def get_stock_moves_for_picking(self, picking_id):
        if picking_id == 0:
            return False

        query = 'select p.product_tmpl_id as product_id, sv.quantity as product_qty, sm.product_uom_qty ordered_qty, ' \
                'sv.unit_cost as price_unit, sm.id as id ' \
                'from stock_valuation_layer sv ' \
                'join stock_move sm on sv.stock_move_id = sm.id ' \
                'join product_product p on sv.product_id = p.id ' \
                'where sm.picking_id = %s;'
        self.env.cr.execute(query, (picking_id,))
        dataset = self.env.cr.dictfetchall()
        return dataset
