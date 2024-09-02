 # Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    'name': 'Complemento de impuestos locales para México',
    'version': '15.0.220429',
    'author': "ECOSOFT, S. DE R.L. DE C.V.",
    'website': "http://www.ecosoft.com.mx",
    'category': 'Hidden',
    'summary': 'Complemento de impuestos locales para México',
    'depends': [
        'l10n_mx_edi',
    ],
    'data': [
        "data/l10n_mx_edi_implocal.xml",
        "data/account_tax_data.xml",
    ],
    'demo': [
    ],
    'installable': True,
    'auto_install': False,
}
