# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, models


class MrpCostStructureCausa(models.AbstractModel):
    _inherit = 'report.mrp_account_enterprise.mrp_cost_structure'

    def get_lines(self, productions):
        res = super(MrpCostStructureCausa, self).get_lines(productions)
        for k in range(len(res)) :        
            product = res[k].get('product', False)
            currency = res[k].get('currency', False)
            purchase_orders_cost = []
            purchase_order_total_cost = 0.0
            if product:            
                mos = productions.filtered(lambda m: m.product_id == product)                
                for mo in mos:
                    for work_order in mo.workorder_ids: 
                        if work_order.is_subcontractig: 
                            for order in work_order.purchase_ids.filtered(lambda x: x.state in ('done')):
                                if currency != order.currency_id:
                                    amount = order.currency_id._convert(order.amount_untaxed,
                                                                        currency, mo.company_id,
                                                                        order.date_order or fields.Date.today())
                                else:
                                    amount = order.amount_untaxed
                                
                                purchase_orders_cost.append({
                                    'reference': order.name,
                                    'date_order': order.date_order,
                                    'partner_name': order.partner_id.name,
                                    'product_name': order.order_line[0].product_id.name,
                                    'total_cost': amount
                                })
                                purchase_order_total_cost += amount
            res[k]['purchase_orders_cost'] = purchase_orders_cost
            res[k]['purchase_order_total_cost'] = purchase_order_total_cost
        return res    
        