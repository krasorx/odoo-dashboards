# -*- coding: utf-8 -*-
{
    'name': 'BOM Dashboard',
    'version': '19.0.1.0.0',
    'category': 'Manufacturing',
    'summary': 'Multi-level BOM dashboard with structure and active MOs views',
    'depends': ['mrp', 'web'],
    'data': [
        'security/ir.model.access.csv',
        'views/bom_dashboard_menu.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'bom_dashboard/static/src/js/components/bom_colors.js',
            'bom_dashboard/static/src/js/components/BomProductCard.js',
            'bom_dashboard/static/src/js/components/MoBomCard.js',
            'bom_dashboard/static/src/js/components/BomLevelColumn.js',
            'bom_dashboard/static/src/js/components/BomSidebar.js',
            'bom_dashboard/static/src/js/components/BomStructureView.js',
            'bom_dashboard/static/src/js/components/BomMoView.js',
            'bom_dashboard/static/src/js/components/BomDashboard.js',
            'bom_dashboard/static/src/js/bom_dashboard_action.js',
        ],
    },
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}
