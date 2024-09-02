# -*- coding: utf-8 -*-

from odoo import api, models
import logging

_logger = logging.getLogger(__name__)


class ResBaseConfigSettings(models.TransientModel):
    _name = "opus.config.settings"
    _inherit = "res.config.settings"

    @api.model
    def set_required_parameters(self):
        _logger.info("====> Estableciendo parámetros requeridos <====")
        values = {
            'group_uom': True,
            'group_stock_multi_locations': True,
            'group_analytic_accounting': True,
            'group_analytic_tags': True}
        res_config_settings = self.env['res.config.settings']
        if 'product_type_default' in res_config_settings._fields and \
                not res_config_settings.product_type_default:
            values['product_type_default'] = 'product'
        settings = self.env['res.config.settings'].create(values)
        settings.execute()
        _logger.info("====> ... Terminado. <====")
