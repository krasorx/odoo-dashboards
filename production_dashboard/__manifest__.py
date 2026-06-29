# -*- coding: utf-8 -*-
{
    'name': 'Production Dashboard',
    'version': '19.0.1.0.0',
    'category': 'Manufacturing',
    'summary': 'Dashboard OWL de estimación de producción con caché inteligente',
    'author': 'krasorx',
    'depends': ['mrp', 'sale', 'purchase', 'stock', 'product', 'web'],
    'data': [
        'security/ir.model.access.csv',
        'data/config_parameter.xml',
        'data/ir_cron.xml',
        'views/estimation_menu.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'production_dashboard/static/src/css/dashboard.css',
            'production_dashboard/static/src/js/cdn_loader.js',
            'production_dashboard/static/src/js/components/KpiCards.js',
            'production_dashboard/static/src/js/components/CostBreakdownChart.js',
            'production_dashboard/static/src/js/components/ComponentsTable.js',
            'production_dashboard/static/src/js/components/HistoryPanel.js',
            'production_dashboard/static/src/js/components/EstimationFilters.js',
            'production_dashboard/static/src/js/components/AiAnalysisPanel.js',
            'production_dashboard/static/src/js/components/EstimationDashboard.js',
            'production_dashboard/static/src/js/estimation_action.js',
        ],
    },
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}
