# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    'name': 'Complemento de impuestos locales fijos para México',
    'version': '15.0.220429',
    'author': "ECOSOFT, S. DE R.L. DE C.V.",
    'website': "http://www.ecosoft.com.mx",
    'summary': 'Complemento de impuestos locales fijos para México',
    'depends': [
        'l10n_mx_edi',
        'ecosoft_impuestoslocales'
    ],
    'data': [
        "data/l10n_mx_edi_implocal.xml",
        'security/ir.model.access.csv',
        'wizard/wizard_account_tax_local_view.xml',
        'views/account_tax_views.xml',
    ],
    'demo': [
    ],
    'installable': True,
    'auto_install': False,
}
