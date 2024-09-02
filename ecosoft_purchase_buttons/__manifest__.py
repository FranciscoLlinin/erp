# -*- coding: utf-8 -*-
{
    'name': "Botones App Compras",
    'summary': "Grupo usuario a botones Compra",
    'description': """
Este modulo crea grupos de seguridad y los asigna a botones como sigue:

   - Puede Validar Acuerdo de Compra: Para accesar boton "Validar" en Acuerdo de Compra
   - Puede Confirmar Solicitud de Presupuesto: Para accesar boton "Confirmar Pedido" en Solicitud de Presupuesto
   - Puede Desbloquear Pedido de Compra: Para accesar boton "Desbloquear" en Pedido de Compra
    """,
    'author': "ECOSOFT, S. DE R.L. DE C.V.",
    'website': "http://www.ecosoft.com.mx",
    'category': 'EcoSoft',
    'version': '15.0.0.0',
    'depends': ['purchase', 'purchase_requisition'],
    'data': [
        'security/purchase_security.xml',
        'views/purchase_requisition_views.xml',
        'views/purchase_order_views.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'AGPL-3',
}
