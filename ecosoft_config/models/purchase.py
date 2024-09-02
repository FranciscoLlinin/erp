# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models


class PurchaseOrderLineAnalytic(models.Model):
    _inherit = "purchase.order.line"

    def _prepare_stock_moves(self, picking):
        """ Hereda Cuentas y Etiquetas Analiticas de 
            purchase.order.line -> stock.move
            y marcarlas como readonly
        """
        res = super(PurchaseOrderLineAnalytic, self)._prepare_stock_moves(picking)
        for item in res:
            item.update({"read_only_analytic":  True})
            item.update({"account_analytic_id": self.account_analytic_id.id})
            item.update({"analytic_tag_ids": [(6, 0, [tag.id for tag in self.analytic_tag_ids])]})
        return res
