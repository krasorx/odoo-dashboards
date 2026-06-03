# -*- coding: utf-8 -*-
{
    'name': 'KPI Widgets',
    'version': '19.0.2.0.0',
    'category': 'Productivity',
    'summary': 'No-code configurable KPI cards in the header of list and kanban views',
    'depends': ['web'],
    'data': [
        'security/ir.model.access.csv',
        'views/kpi_widget_views.xml',
        'views/kpi_widget_menus.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'kpi_widgets/static/src/kpi_card/kpi_card.js',
            'kpi_widgets/static/src/kpi_band/kpi_band.js',
            'kpi_widgets/static/src/kpi_hook.js',
            'kpi_widgets/static/src/kpi_patch.js',
            'kpi_widgets/static/src/kpi_patch.xml',
        ],
    },
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}
