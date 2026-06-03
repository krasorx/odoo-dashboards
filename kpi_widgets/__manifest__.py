# -*- coding: utf-8 -*-
{
    'name': 'KPI Widgets',
    'version': '19.0.1.0.0',
    'category': 'Productivity',
    'summary': 'Reusable configurable KPI cards in the header of list and kanban views',
    'depends': ['web'],
    'data': [],
    'assets': {
        'web.assets_backend': [
            'kpi_widgets/static/src/kpi_card/kpi_card.js',
            'kpi_widgets/static/src/kpi_band/kpi_band.js',
            'kpi_widgets/static/src/kpi_hook.js',
            'kpi_widgets/static/src/views/kpi_views.js',
            'kpi_widgets/static/src/views/kpi_controllers.xml',
        ],
    },
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}
