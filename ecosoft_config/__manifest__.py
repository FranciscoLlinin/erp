# -*- coding: utf-8 -*-
{
    'name': "Configuraciones ECOSOFT",

    'summary': """
       Configuraciones diversas.""",

    'description': """
Configuraciones diversas
===================================
1) Nuevo boton "Solicitar Transferencia" a nivel Transferencia (stock.picking) que genera una nueva transferencia
   que surtira esta tranferencia.
   Este boton solo es visible cuando:
   - La Transferencia es de tipo de Operacion "Clientes" (outgoing)
   - La Transferencia esta en estatus "En espera" (confirm)
   - La Transferencia NO este bloqueada
2) Campos de Cuenta Analitica y Etiquetas Analiticas a nivel Transferencia (stock.picking) heredables desde
   Pedido de Compra (purchase.order) y Pedido de Venta (sale.order)
3) Heredar Cuenta Analitica y Etiquetas Analiticas de stock.move a account.move cuando la cuenta contable
   sea tipo income o expense
    """,

    'author': "ECOSOFT, S. DE R.L. DE C.V.",
    'website': "http://www.ecosoft.com.mx",

    'category': 'EcoSoft',
    'version': '15.0.0.1',

    # any module necessary for this one to work correctly 
    'depends': ['purchase_stock', 'sale_stock'],

    # always loaded
    'data': [
         'views/stock_views.xml',
         'wizard/wizard_solicitar_transferencia_view.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'AGPL-3',
}
