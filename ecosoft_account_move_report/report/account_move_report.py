from odoo import api, models
import base64

TAX_NAMES = {'001': 'ISR', '002': 'IVA', '003': 'IEPS'}


class ParticularReport(models.AbstractModel):
    _name = 'report.ecosoft_account_move_report.ecosoft_account_entries_rpt'

    def _get_report_values(self, docids, data=None):
        docs = self.env['account.move'].browse(docids)
        total_debit_credit = self.get_total_debit_credit(docs)
        res = {
            'doc_ids': docs.ids,
            'doc_model': 'account.move',
            'data': data,
            'docs': docs,
            'total_debit_credit': total_debit_credit,
        }

        res.update({'invoices': self._get_invoices(docids)})
        res.update({'vendor_taxes': self._get_vendor_taxes(docids)})
        return res

    def get_total_debit_credit(self, docs):
        res = {}
        for doc in docs:
            sum_tot_debit = sum(doc.line_ids.mapped('debit'))
            sum_tot_credit = sum(doc.line_ids.mapped('credit'))
            res.update({doc.id:
                            {'sum_tot_debit': sum_tot_debit,
                             'sum_tot_credit': sum_tot_credit}})
        return res

    def _get_invoices(self, docids):
        docs = self.env['account.move'].browse(docids)
        res = {}
        for doc in docs:
            invoice_recs = self._get_invoice_ids(doc)
            res.update({doc.id: invoice_recs})
        return res

    def _get_vendor_taxes(self, docids):
        docs = self.env['account.move'].browse(docids)
        res = {}
        for doc in docs:
            invoice_recs = self._get_invoice_ids(doc, invoice_type=['in_invoice'])
            data = []
            for inv in invoice_recs:
                attachment_id = inv._get_l10n_mx_edi_signed_edi_document()
                if not attachment_id:
                    continue
                datas = attachment_id._file_read(attachment_id.store_fname)
                cfdi = base64.decodebytes(datas).replace(
                    b'xmlns:schemaLocation', b'xsi:schemaLocation')
                tree = inv.l10n_mx_edi_get_xml_etree(cfdi)

                if hasattr(tree, 'Impuestos') and hasattr(tree.Impuestos, 'Retenciones'):
                    for t in tree.Impuestos.Retenciones.getiterator():
                        tax_code = t.get('Impuesto', t.get('impuesto'))
                        tax_amount = t.get('TasaOCuota', t.get('tasaocuota', False))
                        if tax_code is not None:
                            data.append({'tax_code': tax_code,
                                         'tax_name': '%s: %s' % (tax_code, TAX_NAMES.get(tax_code, False)),
                                         'tax_amount': float(tax_amount) * 100 if tax_amount else False,
                                         'tax': float(t.get('Importe', t.get('importe')))})

                if hasattr(tree, 'Impuestos') and hasattr(tree.Impuestos, 'Traslados'):
                    for t in tree.Impuestos.Traslados.getiterator():
                        tax_code = t.get('Impuesto', t.get('impuesto'))
                        if tax_code is not None:
                            data.append({'tax_code': tax_code,
                                         'tax_name': '%s: %s' % (tax_code, TAX_NAMES.get(tax_code, False)),
                                         'tax_amount': float(t.get('TasaOCuota', t.get('tasaocuota'))) * 100,
                                         'tax': float(t.get('Importe', t.get('importe')))})

            res.update({doc.id: data})
        return res

    def _get_invoice_ids(self, move, invoice_type=['in_invoice', 'out_invoice']):
        ids = []
        if move.move_type in invoice_type and move.l10n_mx_edi_cfdi_uuid:
            for line in move.line_ids:
                if line.move_id.id not in ids:
                    ids.append(line.move_id.id)
        return self.env['account.move'].browse(ids)
