# -*- coding: utf-8 -*-
{
    'name': 'Guides HTML Sharing',
    'version': '19.0.1.0.0',
    'category': 'Productivity/Documentation',
    'summary': 'Upload, organize, version and share AI-generated HTML documentation',
    'author': 'krasorx',
    'depends': ['web', 'mail', 'project', 'portal'],
    'data': [
        'security/guides_security.xml',
        'security/ir.model.access.csv',
        'data/guides_data.xml',
        'wizard/guides_version_wizard_views.xml',
        'views/guides_tag_views.xml',
        'views/guides_folder_views.xml',
        'views/guides_document_views.xml',
        'views/project_task_views.xml',
        'views/guides_menus.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'guides_html_sharing/static/src/guides_browser/guides_browser.scss',
            'guides_html_sharing/static/src/guides_browser/guides_browser.js',
            'guides_html_sharing/static/src/guides_browser/guides_browser.xml',
        ],
    },
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}
