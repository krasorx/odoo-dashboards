# -*- coding: utf-8 -*-
{
    'name': 'KPI Widgets - Stock Picking Example',
    'version': '19.0.1.0.0',
    'category': 'Inventory',
    'summary': 'Example: delivery/receipt KPI cards by status on stock.picking',
    'depends': ['stock', 'kpi_widgets'],
    'data': [
        'views/stock_picking_views.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'kpi_stock_picking/static/src/stock_kpi_list_view.js',
        ],
    },
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}
