# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from datetime import date
from odoo.exceptions import UserError


class Partner(models.Model):
    _inherit = 'res.partner'

    @api.model
    def create(self, vals):
        # vat = vals.get("vat", False)
        # if vat:
        #     vat_upper = vat.upper()
        #     with_vat = self.search([('vat', '=', vat_upper)], limit=1)
        #     vals["vat"] = vat_upper
        #     if with_vat:
        #         raise UserError(_(f'Ya existe un contacto con el mismo RFC ({with_vat.name})'))
        vat_upper = self._validate_vat(vals.get('vat', False))
        if vat_upper:
            vals['vat'] = vat_upper
        res = super(Partner, self).create(vals)             
        return res

    def write(self, values):        
        # vat = values.get("vat", False)
        # if vat:
        #     vat_upper = vat.upper()
        #     with_vat = self.search([('vat', '=', vat_upper), ('id', '!=' , self.id)], limit=1)
        #     values["vat"] = vat_upper
        #     if with_vat:
        #         raise UserError(_(f'Ya existe un contacto con el mismo RFC ({with_vat.name})'))
        vat_upper = self._validate_vat(values.get('vat', False))
        if vat_upper:
            values['vat'] = vat_upper
        res = super(Partner, self).write(values)
        return res

    def _validate_vat(self, vat, is_new=True):
        vat_upper = False
        if vat:
            vat_upper = vat.upper()
            domain = [('vat', '=', vat_upper)]
            if not is_new:
                domain.append(('id', '!=', self.id))
            has_vat = self.search(domain, limit=1)
            if has_vat:
                raise UserError(_(f'Ya existe un contacto con el mismo RFC ({has_vat.name})'))
        return vat_upper
