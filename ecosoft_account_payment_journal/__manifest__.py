# -*- coding: utf-8 -*-
{
    'name': "Contabilidad - Vista Registrar Pago",

    'summary': """
       Modifica Vista para Registrar Pago""",

    'description': """
Este modulo modifica la vista para Registro de Pago, permitiendo 
busqueda de Diario de Pago.
    """,

    'author': "ECOSOFT, S. DE R.L. DE C.V.",
    'website': "http://www.ecosoft.com.mx",

    'category': 'EcoSoft',
    'version': '15.0.0.0',

    'depends': ['account', 'payment','l10n_mx_edi'],

    'data': [
        'views/account_payment_view.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'AGPL-3',
}
