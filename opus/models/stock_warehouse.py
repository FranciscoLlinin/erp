from odoo import models, fields, api
import logging
_logger = logging.getLogger(__name__)


class Warehouse(models.Model):
    _name = "stock.warehouse"
    _inherit = "stock.warehouse"

    code = fields.Char('Short Name', required=True, size=100, help="Short name used to identify your warehouse")
