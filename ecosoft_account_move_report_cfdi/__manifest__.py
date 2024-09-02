{
    'name': 'Reporte Poliza Contable con CFDi',
    'version': '15.0.0.20221005',
    'author': 'ECOSOFT, S. DE R.L. DE C.V.',
    'category': 'Accouting',
    'website': 'http://www.ecosoft.com.mx/',
    'depends': [
        'account',
        'ecosoft_account_move_report',
    ],
    'demo': [],
    'data': [
        'views/account_move_report.xml',
        'views/account_reports.xml',
        'views/report_templates.xml',
        'views/ir_qweb_widget_templates.xml'
    ],
    'installable': True,
    'auto_install': False,
    'license': 'Other proprietary'
}
