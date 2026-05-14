# -*- coding: utf-8 -*-
from odoo import models, fields


class MrpTeam(models.Model):
    _name = 'mrp.team'
    _description = 'MRP Team'
    _order = 'name'

    name = fields.Char(string='Team Name', required=True)
    member_ids = fields.Many2many(
        'hr.employee',
        'mrp_team_employee_rel',
        'team_id',
        'employee_id',
        string='Members',
    )
    color = fields.Integer(string='Color Index', default=0)
    active = fields.Boolean(default=True)
