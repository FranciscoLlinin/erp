# -*- coding: utf-8 -*-

from odoo import api, models, fields, _
from datetime import datetime

MONTH_NAME_SHORT_ES = ['', 'Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dic']


class AccountMove(models.Model):
    _inherit = 'account.move'

    l10n_mx_edi_cfdi_date_invoice = fields.Char(string='Fecha Timbrado', copy=False, readonly=True,
                                                help='Fecha timbrado.',
                                                compute='_compute_cfdi_values')
    l10n_mx_edi_cfdi_customer_name = fields.Char(string='Razon Social Cliente', copy=False, readonly=True,
                                                 help='Razon Social Cliente.',
                                                 compute='_compute_cfdi_values')
    l10n_mx_edi_cfdi_supplier_name = fields.Char(string='Razon Social Proveedor', copy=False, readonly=True,
                                                 help='Razon Social Proveedor.',
                                                 compute='_compute_cfdi_values')
    l10n_mx_edi_cfdi_serie = fields.Char(string='Serie', copy=False, readonly=True,
                                         help='Serie.',
                                         compute='_compute_cfdi_values')
    l10n_mx_edi_cfdi_folio = fields.Char(string='Folio', copy=False, readonly=True,
                                         help='Folio.',
                                         compute='_compute_cfdi_values')

    @api.depends('edi_document_ids')
    def _compute_cfdi_values(self):
        res = super(AccountMove, self)._compute_cfdi_values()
        # self.l10n_mx_edi_cfdi_date_invoice = ''
        # self.l10n_mx_edi_cfdi_customer_name = ''
        # self.l10n_mx_edi_cfdi_supplier_name = ''
        # self.l10n_mx_edi_cfdi_serie = ''
        # self.l10n_mx_edi_cfdi_folio = ''

        for invoice in self:
            cfdi_infos = invoice._l10n_mx_edi_decode_cfdi()
            cfdi_node = cfdi_infos.get('cfdi_node')
            if cfdi_node is None:
                continue

            invoice.l10n_mx_edi_cfdi_supplier_name = cfdi_node.Emisor.get('Nombre', cfdi_node.Emisor.get('nombre'))
            invoice.l10n_mx_edi_cfdi_customer_name = cfdi_node.Receptor.get('Nombre', cfdi_node.Receptor.get('nombre'))
            invoice.l10n_mx_edi_cfdi_folio = cfdi_node.get('Folio', cfdi_node.get('folio'))
            invoice.l10n_mx_edi_cfdi_serie = cfdi_node.get('Serie', cfdi_node.get('serie'))

            stamp_date_str = cfdi_infos.get('stamp_date')
            stamp_date_parts = stamp_date_str.split(' ')
            if len(stamp_date_parts) > 0:
                date = datetime.strptime(stamp_date_parts[0], '%Y-%m-%d')
                invoice.l10n_mx_edi_cfdi_date_invoice = '%s/%s/%s' % (
                    date.strftime('%d'),
                    MONTH_NAME_SHORT_ES[int(date.strftime('%m'))],
                    date.strftime('%Y'))

        return res
