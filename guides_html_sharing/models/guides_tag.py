# -*- coding: utf-8 -*-
from odoo import fields, models


class GuidesTag(models.Model):
    _name = 'guides.tag'
    _description = 'Guide Tag'
    _order = 'name'

    name = fields.Char(required=True)
    color = fields.Integer(string='Color')

    _name_uniq = models.Constraint(
        'unique(name)', 'A tag with this name already exists.')
