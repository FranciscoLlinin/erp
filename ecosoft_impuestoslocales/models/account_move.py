from lxml import etree

from odoo import models


class AccountMove(models.Model):
    _inherit = 'account.move'

    def _l10n_mx_edi_create_cfdi(self):
        result = super(AccountMove, self)._l10n_mx_edi_create_cfdi()
        cfdi = result.get('cfdi')
        if not cfdi:
            return result
        cfdi = self.l10n_mx_edi_get_xml_etree(cfdi)
        if 'implocal' not in cfdi.nsmap:
            return result
        cfdi.attrib['{http://www.w3.org/2001/XMLSchema-instance}schemaLocation'] = '%s %s %s' % (
            cfdi.get('{http://www.w3.org/2001/XMLSchema-instance}schemaLocation'),
            'http://www.sat.gob.mx/implocal',
            'http://www.sat.gob.mx/sitio_internet/cfd/implocal/implocal.xsd')
        result['cfdi'] = etree.tostring(cfdi, pretty_print=True, xml_declaration=True, encoding='UTF-8')
        return result

    def get_tax_amount(self, tax):
        total = 0
        lines = [line for line in self.invoice_line_ids.filtered(
            lambda l: l.mapped('tax_ids').filtered(
                lambda r: r == tax))]
        total += sum(abs(tax.amount / 100) * abs(line.amount_currency) for line in lines)
        return total

    def get_total_local_transferred(self):
        total = 0
        for line in self.invoice_line_ids:
            taxes = line.mapped('tax_ids').filtered(
                lambda r: r.invoice_repartition_line_ids.filtered(
                    lambda rep: rep.tag_ids and rep.tag_ids[0].name.lower() == 'local') and r.amount > 0)
            total += sum(abs(t.amount / 100) * abs(line.amount_currency) for t in taxes)
        return total

    def get_total_local_withhold(self):
        total = 0
        for line in self.invoice_line_ids:
            taxes = line.mapped('tax_ids').filtered(
                lambda r: r.invoice_repartition_line_ids.filtered(
                    lambda rep: rep.tag_ids and rep.tag_ids[0].name.lower() == 'local') and r.amount < 0)
            total += sum(abs(t.amount / 100) * abs(line.amount_currency) for t in taxes)
        return total
