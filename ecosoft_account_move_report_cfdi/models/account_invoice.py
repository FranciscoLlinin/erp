# -*- coding: utf-8 -*-

import base64
from odoo import api, models, fields, _
from datetime import datetime

MONTH_NAME_SHORT_ES = ['', 'Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dic']

class AccountInvoice(models.Model):
    _name = 'account.move'
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

    # @api.multi
    # @api.depends('l10n_mx_edi_cfdi_name')
    @api.depends('edi_document_ids')
    def _compute_cfdi_values(self):
        '''Fill the invoice fields from the cfdi values.
        '''
        res = super(AccountInvoice, self)._compute_cfdi_values()
        for inv in self:
            attachment_id = inv.l10n_mx_edi_retrieve_last_attachment()
            if not attachment_id:
                continue
                
            datas = attachment_id._file_read(attachment_id.store_fname)
            inv.l10n_mx_edi_cfdi = datas
            cfdi = base64.decodestring(datas).replace(
                b'xmlns:schemaLocation', b'xsi:schemaLocation')
            tree = inv.l10n_mx_edi_get_xml_etree(cfdi)
            # if already signed, extract uuid
            tfd_node = inv.l10n_mx_edi_get_tfd_etree(tree)
            inv.l10n_mx_edi_cfdi_supplier_name = tree.Emisor.get(
                'Nombre', tree.Emisor.get('nombre'))
            inv.l10n_mx_edi_cfdi_customer_name = tree.Receptor.get(
                'Nombre', tree.Receptor.get('nombre'))                
            inv.l10n_mx_edi_cfdi_serie = tree.get('Serie', tree.get('serie'))
            inv.l10n_mx_edi_cfdi_folio = tree.get('Folio', tree.get('folio'))
            
            # Format XML: Fecha="2020-06-15T00:21:10"
            tfd_node = inv.l10n_mx_edi_get_tfd_etree(tree)
            if tfd_node is not None:
                date_invoice_str = tfd_node.get('FechaTimbrado')
                date_invoice_parts = date_invoice_str.split('T')           
                if len(date_invoice_parts) > 0:
                    date = datetime.strptime(date_invoice_parts[0], '%Y-%m-%d')                
                    inv.l10n_mx_edi_cfdi_date_invoice = '%s/%s/%s'%(date.strftime('%d'), MONTH_NAME_SHORT_ES[int(date.strftime('%m'))], date.strftime('%Y'))
                    
        return res

