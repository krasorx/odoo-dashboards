# -*- coding: utf-8 -*-
from odoo import api, fields, models
from odoo.exceptions import ValidationError

NUMERIC_TYPES = ('integer', 'float', 'monetary')
MINMAX_TYPES = ('integer', 'float', 'monetary', 'date', 'datetime')


class KpiWidget(models.Model):
    _name = 'kpi.widget'
    _description = 'KPI Widget Definition'
    _order = 'sequence, id'

    name = fields.Char(required=True)
    active = fields.Boolean(default=True)
    sequence = fields.Integer(default=10)

    model_id = fields.Many2one('ir.model', string='Model', required=True, ondelete='cascade')
    model_name = fields.Char(related='model_id.model', store=True, index=True)

    card_type = fields.Selection(
        [('aggregate', 'Single value'), ('group_by', 'Group by field')],
        default='aggregate', required=True)

    groupby_field_id = fields.Many2one(
        'ir.model.fields', string='Group by field', ondelete='cascade',
        domain="[('model_id', '=', model_id)]")
    measure_field_id = fields.Many2one(
        'ir.model.fields', string='Measure field', ondelete='cascade',
        domain="[('model_id', '=', model_id)]",
        help="Field to aggregate. Leave empty to count records.")
    aggregate = fields.Selection(
        [('count', 'Count'), ('sum', 'Sum'), ('avg', 'Average'),
         ('max', 'Max'), ('min', 'Min')],
        default='count', required=True)

    domain = fields.Char(default='[]', help="Extra filter applied to this card.")
    label = fields.Char(translate=True, help="Card title (single value). Fallback to name.")
    value_format = fields.Selection(
        [('integer', 'Integer'), ('float', 'Float'), ('monetary', 'Monetary'),
         ('percentage', 'Percentage'), ('raw', 'Raw')],
        string='Format', help="Leave empty for automatic.")
    color = fields.Char(help="Hex color, e.g. #22c55e")
    icon = fields.Char(help="FontAwesome class, e.g. fa fa-truck")

    clickable = fields.Boolean(default=True)
    show_in_list = fields.Boolean(default=True)
    show_in_kanban = fields.Boolean(default=True)

    @api.onchange('model_id')
    def _onchange_model_id(self):
        self.groupby_field_id = False
        self.measure_field_id = False

    @api.constrains('card_type', 'groupby_field_id', 'aggregate', 'measure_field_id')
    def _check_config(self):
        for rec in self:
            if rec.card_type == 'group_by' and not rec.groupby_field_id:
                raise ValidationError("Group-by cards require a 'Group by field'.")
            if rec.aggregate in ('sum', 'avg') and (
                    not rec.measure_field_id or rec.measure_field_id.ttype not in NUMERIC_TYPES):
                raise ValidationError("Sum/Average require a numeric Measure field.")
            if rec.aggregate in ('max', 'min') and (
                    not rec.measure_field_id or rec.measure_field_id.ttype not in MINMAX_TYPES):
                raise ValidationError("Max/Min require a numeric or date Measure field.")
