# -*- coding: utf-8 -*-
{
    'name': "Ajustes a Chatter y Followers mixin en CRM",

    'summary': """
       Ajustes a Chatter y Followers mixin en CRM""",

    'description': """
       Ajustes a Chatter y Followers mixin en CRM.
        No agrear automaticamente como follower a clientes
        No enviar por defecto email notification chatter post
        Modificar plantilla email enviada a nuevo follower
    """,

    'author': "EcoSoft",
    'website': "http://www.ecosoft.com.mx",
    'category': 'EcoSoft',
    'version': '1.0',

    # any module necessary for this one to work correctly 
    'depends': ['crm', 'mail'],

    # always loaded
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'AGPL-3',
    'qweb': [
        'static/src/xml/chatter.xml',
    ],
    'assets': {
        'web.assets_backend': [
            '/ecosoft_account_proration/static/src/js/tree_view_button.js',
        ],
    }
}
