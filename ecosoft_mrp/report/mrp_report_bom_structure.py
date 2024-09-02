# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, models, fields, SUPERUSER_ID, _
from odoo.tools import float_round


class ReportBomStructureCausa(models.AbstractModel):
    _inherit = 'report.mrp.report_bom_structure'

    def _get_bom(self, bom_id=False, product_id=False, line_qty=False, line_id=False, level=False):
        res = super(ReportBomStructureCausa, self)._get_bom(bom_id=bom_id, product_id=product_id, line_qty=line_qty,
                                                            line_id=line_id, level=level)
        bom = self.env['mrp.bom'].browse(bom_id)
            
        bom_quantity = res.get('bom_qty', 0)
        external_services = self._get_external_services_line(bom.routing_id, bom_quantity / bom.product_qty, 0)
        res['external_services'] = external_services
        res['external_services_cost'] =  sum([op['total'] for op in external_services])
        res['external_services_qty'] =  sum([op['prod_qty'] for op in external_services])
        res['total'] += res['external_services_cost']
        return res
    
    def _get_external_services_line(self, routing, qty, level):
        external_services = []
        total = 0.0
        for operation in routing.operation_ids:
            if operation.workcenter_id.is_subcontractig:      
                
                FiscalPosition = self.env['account.fiscal.position']
                fpos = FiscalPosition.get_fiscal_position(operation.workcenter_id.partner_id.id)
                fpos = FiscalPosition.browse(fpos)
        
                if self.env.uid == SUPERUSER_ID:
                    company_id = self.env.user.company_id.id
                    taxes_id = fpos.map_tax(operation.workcenter_id.product_id.supplier_taxes_id.
                                            filtered(lambda r: r.company_id.id == company_id))
                else:
                    taxes_id = fpos.map_tax(operation.workcenter_id.product_id.supplier_taxes_id)
            
                seller = operation.workcenter_id.product_id._select_seller(
                    partner_id=operation.workcenter_id.partner_id,
                    quantity=qty)
                price = self.env['account.tax'].\
                    _fix_tax_included_price_company(seller.price,
                                                    operation.workcenter_id.product_id.supplier_taxes_id,
                                                    taxes_id,
                                                    operation.company_id) if seller else operation.workcenter_id.product_id.standard_price
                price = seller.currency_id._convert(price, operation.company_id.currency_id, operation.company_id,
                                                    fields.Date.today())
                
                external_services.append({
                    'level': level or 0,
                    'operation': operation,
                    'partner_id': operation.workcenter_id.partner_id,
                    'product_id': operation.workcenter_id.product_id,
                    'code': operation.workcenter_id.product_id.name,
                    'prod_cost': self.env.user.company_id.currency_id.round(price),
                    'prod_qty': qty,
                    'total': self.env.user.company_id.currency_id.round(qty * price),
                })
        return external_services
     
    @api.model
    def get_externos(self, bom_id=False, qty=0, level=0):
        bom = self.env['mrp.bom'].browse(bom_id)
        lines = self._get_external_services_line(bom.routing_id, qty / bom.product_qty, level)
        values = {
            'bom_id': bom_id,
            'currency': self.env.user.company_id.currency_id,
            'external_services': lines,
        }
        return self.env.ref('ecosoft_mrp.report_mrp_external_line').render({'data': values})
 
    """ Override completamente (sin invocar super method) """
    def _get_pdf_line(self, bom_id, product_id=False, qty=1, child_bom_ids=[], unfolded=False):

        data = self._get_bom(bom_id=bom_id, product_id=product_id.id, line_qty=qty)

        def get_sub_lines(bom, product_id, line_qty, line_id, level):
            data = self._get_bom(bom_id=bom.id, product_id=product_id.id, line_qty=line_qty, line_id=line_id, level=level)
            bom_lines = data['components']
            lines = []
            for bom_line in bom_lines:
                lines.append({
                    'name': bom_line['prod_name'],
                    'type': 'bom',
                    'quantity': bom_line['prod_qty'],
                    'uom': bom_line['prod_uom'],
                    'prod_cost': bom_line['prod_cost'],
                    'bom_cost': bom_line['total'],
                    'level': bom_line['level'],
                    'code': bom_line['code']
                })
                if bom_line['child_bom'] and (unfolded or bom_line['child_bom'] in child_bom_ids):
                    line = self.env['mrp.bom.line'].browse(bom_line['line_id'])
                    lines += (get_sub_lines(line.child_bom_id, line.product_id, bom_line['prod_qty'], line, level + 1))
            if data['operations']:
                lines.append({
                    'name': _('Operations'),
                    'type': 'operation',
                    'quantity': data['operations_time'],
                    'uom': _('minutes'),
                    'bom_cost': data['operations_cost'],
                    'level': level,
                })
                for operation in data['operations']:
                    if unfolded or 'operation-' + str(bom.id) in child_bom_ids:
                        lines.append({
                            'name': operation['name'],
                            'type': 'operation',
                            'quantity': operation['duration_expected'],
                            'uom': _('minutes'),
                            'bom_cost': operation['total'],
                            'level': level + 1,
                        })                       
                                 
            if data['external_services']:
                lines.append({
                    'name': 'Servicios Externos',
                    'type': 'externo',
                    'uom': 'minutes',
                    'bom_cost': data['external_services_cost'], 
                    'level': level,
                })
                for externo in data['external_services']:
                    if unfolded or 'externo-' + str(bom.id) in child_bom_ids:
                        lines.append({
                            'name': externo['partner_id'].name,  # externo['name'],
                            'type': 'externo',
                            'quantity': externo['prod_qty'],
                            'prod_cost': externo['prod_cost'],
                            'uom': 'minutes',
                            'bom_cost': externo['total'],
                            'level': level + 1,
                        })
            return lines

        bom = self.env['mrp.bom'].browse(bom_id)
        product = product_id or bom.product_id or bom.product_tmpl_id.product_variant_id
        pdf_lines = get_sub_lines(bom, product, qty, False, 1)
        data['components'] = []
        data['lines'] = pdf_lines
        return data
