# -*- coding: utf-8 -*-
from odoo import models, fields


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    mrp_team_ids = fields.Many2many(
        'mrp.team',
        'mrp_team_employee_rel',
        'employee_id',
        'team_id',
        string='MRP Teams',
    )
