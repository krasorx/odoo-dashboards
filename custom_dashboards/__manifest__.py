# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Custom Dashboards',
    'version': '18.0.1.0.0',
    'category': 'Website',
    'summary': 'Custom dashboard pages with Tailwind CSS for business metrics',
    'description': """
        This module provides custom dashboard pages with real-time business metrics:
        
        * Invoiced amount this month
        * Manufacturing orders completed
        * Sales pending delivery
        * Overdue invoices
        * Top products by sales
        * Monthly sales charts
        
        Built with Tailwind CSS and Odoo 18 OWL framework.
    """,
    'author': 'Your Company',
    'website': '',
    'license': 'LGPL-3',
    'depends': ['website', 'account', 'sale', 'web'],
    'data': [
        'views/templates.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'custom_dashboards/custom_dashboards.css',
        ],
    },
    'demo': [],
    'installable': True,
    'application_manifest': True,
}
