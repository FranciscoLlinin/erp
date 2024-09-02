# -*- coding: utf-8 -*-
{
    'name': "Reporte Historico de Pagos",

    'summary': """
        Este modulo personaliza reporte contable Historico de Pagos
    """,

    'description': """
        Este modulo personaliza reporte contable Historico de Pagos 
        Contabilidad->Informes->Informes de socios->Historico de Pagos.
        
        Agrega filtro por Moneda
        
        Cuando el reporte se pide en una moneda especifica unicamente se 
        desplegaran los movientos realizados en dicha moneda y en su moneda 
        orginal.
        
        Cuando el reporte se pide en todas las monedas se despliega el reporte 
        nativo de Odoo, todas las transacciones convertidas a la moneda de la 
        Compania.
    """,

    'author': "ECOSOFT, S. DE R.L. DE C.V.",
    'website': "http://www.ecosoft.com.mx",

    'category': 'EcoSoft',
    'version': '15.0.220317',

    # any module necessary for this one to work correctly 'website',
    'depends': ['account', 'account_reports'],

    # always loaded
    'data': [
        'views/search_template_view.xml',
    ],
}
