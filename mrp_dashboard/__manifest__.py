# -*- coding: utf-8 -*-
{
    'name': 'MRP Dashboard',
    'version': '19.0.1.0.0',
    'category': 'Manufacturing',
    'summary': 'Weekly manufacturing orders dashboard with team filters and auto-refresh',
    'depends': ['mrp', 'hr', 'web'],
    'data': [
        'security/ir.model.access.csv',
        'views/mrp_team_views.xml',
        'views/hr_employee_views.xml',
        'views/mrp_dashboard_menu.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'mrp_dashboard/static/src/js/components/MoCard.js',
            'mrp_dashboard/static/src/js/components/WeekColumn.js',
            'mrp_dashboard/static/src/js/components/MrpDashboard.js',
            'mrp_dashboard/static/src/js/mrp_dashboard_action.js',
        ],
    },
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}
