# -*- coding: utf-8 -*-
from . import controllers


def post_init_hook(env):
    """Find the base mrp.production list view and add js_class to it."""
    View = env['ir.ui.view'].sudo()

    base_view = View.search([
        ('model', '=', 'mrp.production'),
        ('type', '=', 'list'),
        ('inherit_id', '=', False),
    ], order='priority asc', limit=1)

    if not base_view:
        return

    # Avoid creating duplicate if already installed
    if View.search([
        ('name', '=', 'mrp.production.list.stats.jsclass'),
        ('model', '=', 'mrp.production'),
    ]):
        return

    View.create({
        'name': 'mrp.production.list.stats.jsclass',
        'model': 'mrp.production',
        'type': 'list',
        'inherit_id': base_view.id,
        'arch_base': (
            '<list position="attributes">'
            '<attribute name="js_class">mrp_production_list</attribute>'
            '</list>'
        ),
    })
