# -*- coding: utf-8 -*-
import logging
from odoo import api, models
from odoo.tools.safe_eval import safe_eval

_logger = logging.getLogger(__name__)

NUMERIC_TYPES = ('integer', 'float', 'monetary')


class Base(models.AbstractModel):
    _inherit = 'base'

    @api.model
    def get_view_kpis(self, domain, view_type=None):
        """Compute KPI cards for this model from active kpi.widget config.

        Must be @api.model: called from the client via orm.call, where call_kw
        passes the first positional arg straight through only for model methods.
        Config is read with sudo; aggregates run as the current user (respecting
        record rules). Returns a list of card dicts.
        """
        widgets = self.env['kpi.widget'].sudo().search([
            ('model_name', '=', self._name), ('active', '=', True),
        ])
        if view_type == 'list':
            widgets = widgets.filtered('show_in_list')
        elif view_type == 'kanban':
            widgets = widgets.filtered('show_in_kanban')

        base_domain = domain or []
        cards = []
        for w in widgets:
            try:
                cards.extend(self._kpi_compute_widget(w, base_domain))
            except Exception as e:  # noqa: BLE001 - one bad card must not break the band
                _logger.warning("kpi.widget %s failed for %s: %s", w.id, self._name, e)
        return cards

    @api.model
    def _kpi_compute_widget(self, widget, base_domain):
        extra = safe_eval(widget.domain or '[]')
        full = list(base_domain) + list(extra)
        measure_field = widget.measure_field_id.name or False
        agg = widget.aggregate
        measure_spec = '__count' if (agg == 'count' or not measure_field) else f'{measure_field}:{agg}'
        fmt = widget.value_format or self._kpi_default_format(widget)
        color, icon = widget.color or None, widget.icon or None

        if widget.card_type == 'aggregate':
            rows = self.env[self._name]._read_group(full, [], [measure_spec])
            value = rows[0][0] if rows else 0
            card = {
                'id': f'w{widget.id}',
                'label': widget.label or widget.name,
                'value': value or 0,
                'format': fmt,
            }
            if color:
                card['color'] = color
            if icon:
                card['icon'] = icon
            if widget.clickable:
                card['domain'] = extra
            return [card]

        # group_by
        gb = widget.groupby_field_id.name
        rows = self.env[self._name]._read_group(full, [gb], [measure_spec])
        field = self.env[self._name]._fields[gb]
        cards = []
        for row in rows:
            group_value, measure = row[0], row[1]
            label, key = self._kpi_group_label_key(field, group_value)
            card = {
                'id': f'w{widget.id}_{key}',
                'label': label,
                'value': measure or 0,
                'format': fmt,
            }
            if color:
                card['color'] = color
            if icon:
                card['icon'] = icon
            if widget.clickable:
                card['domain'] = list(extra) + [(gb, '=', key)]
            cards.append(card)
        return cards

    @api.model
    def _kpi_group_label_key(self, field, value):
        """Return (display label, domain key) for a read_group group value."""
        if field.type == 'many2one':
            return (value.display_name if value else 'None'), (value.id if value else False)
        if field.type == 'selection':
            selection = dict(field._description_selection(self.env))
            return selection.get(value, value if value not in (None, False) else 'None'), value
        return (str(value) if value not in (None, False) else 'None'), value

    @api.model
    def _kpi_default_format(self, widget):
        if widget.aggregate == 'count' or not widget.measure_field_id:
            return 'integer'
        if widget.measure_field_id.ttype == 'monetary':
            return 'monetary'
        return 'float'
