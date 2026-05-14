# -*- coding: utf-8 -*-
{
    'name': 'MRP Stats Header',
    'version': '19.0.1.0.0',
    'category': 'Manufacturing',
    'summary': 'Stats banner on the manufacturing orders list view — counts by state with week filter',
    'depends': ['mrp', 'web'],
    'data': [
        'security/ir.model.access.csv',
    ],
    'assets': {
        'web.assets_backend': [
            'mrp_stats_header/static/src/xml/mrp_stats_list_controller.xml',
            'mrp_stats_header/static/src/js/components/MrpStatsCard.js',
            'mrp_stats_header/static/src/js/components/MrpStatsBanner.js',
            'mrp_stats_header/static/src/js/mrp_stats_list_controller.js',
            'mrp_stats_header/static/src/js/mrp_stats_list_view.js',
        ],
    },
    'post_init_hook': 'post_init_hook',
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}
