# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo import api, fields, models


class StockMoveAnalyticAccount(models.Model):
    _inherit = "stock.move"
  
    account_analytic_id = fields.Many2one('account.analytic.account', string='Cuenta Analitica')
    analytic_tag_ids = fields.Many2many('account.analytic.tag', string='Etiquetas Analiticas')
    read_only_analytic = fields.Boolean(default=False)

    # --------------------------------------------------
    # ORM
    # --------------------------------------------------

    @api.model_create_multi
    def create(self, vals_list):
        lines = super(StockMoveAnalyticAccount, self).create(vals_list)
        # TBD heredar info. debiera estar en sale.order.line._prepare_procurement_values()
        # sin embargo por alguna razon no las estaba heredando, por cuestiones de tiempo\
        # lo puse aqui.
        for line in lines.filtered(lambda x: x.sale_line_id):
            line.account_analytic_id = line.sale_line_id.order_id.analytic_account_id.id
            line.analytic_tag_ids = line.sale_line_id.analytic_tag_ids
            line.read_only_analytic = True
                
        return lines
        
    def _generate_valuation_lines_data(
            self, partner_id, qty, debit_value, credit_value, debit_account_id, credit_account_id, description):
        """ Overridden para heredar cuenta y etiqueta analitica, pero unicamente
            si la cuenta es account.account.user_type_id.internal_group in ('income', 'expense')
        """
        self.ensure_one()
        rslt = super(StockMoveAnalyticAccount, self)._generate_valuation_lines_data(
            partner_id,
            qty,
            debit_value,
            credit_value,
            debit_account_id,
            credit_account_id,
            description)
        
        acc_obj = self.env['account.account']
        
        account = acc_obj.browse(rslt['credit_line_vals']['account_id'])
        if account.user_type_id.internal_group in ('income', 'expense'):
            rslt['credit_line_vals']['analytic_account_id'] = self.account_analytic_id.id
            rslt['credit_line_vals']['analytic_tag_ids'] = [(6, 0, [tag.id for tag in self.analytic_tag_ids])]
        
        account = acc_obj.browse(rslt['debit_line_vals']['account_id'])
        if account.user_type_id.internal_group in ('income', 'expense'):
            rslt['debit_line_vals']['analytic_account_id'] = self.account_analytic_id.id
            rslt['debit_line_vals']['analytic_tag_ids'] = [(6, 0, [tag.id for tag in self.analytic_tag_ids])]
            
        return rslt


class StockPickingValidate(models.Model):
    _inherit = "stock.picking"
                
    related_picking_id = fields.Many2one('stock.picking', string='Movimiento de Stock relacionado', readonly=True, copy=False)

    # --------------------------------------------------
    # Actions
    # --------------------------------------------------

    def action_solicitar_transferencia(self):
        """ Accion para boton "Solicitar Transferencia"
            en stock.picking de salida abre Wizard"""
            
        type_obj = self.env['stock.picking.type']
        company_id = self.env.context.get('company_id') or self.env.user.company_id.id
        types = type_obj.search([('code', '=', 'internal'), ('warehouse_id.company_id', '=', company_id)])
        if not types:
            types = type_obj.search([('code', '=', 'internal'), ('warehouse_id', '=', False)])
        picking_type_id = types[:1]
        
        data = {'picking_id': self.id,
                'location_dest_id': self.location_id.id,
                'picking_type_id': picking_type_id.id }
        
        wiz = self.env['wizard.solicitar.transferencia'].create(data)     
        view_id = self.env['ir.model.data'].get_object_reference('ecosoft_config', 'wizard_solicitar_transferencia_view')[1]
        return {
            'name': 'Transferencias',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'wizard.solicitar.transferencia'  ,
            'view_id': view_id,
            'type': 'ir.actions.act_window',
            'target':'new',
            'context':  dict(self._context or {}),
            'res_id': wiz.id,
            }
