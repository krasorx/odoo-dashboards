# -*- coding: utf-8 -*-
from odoo import models

# state -> card color; list order defines display order.
KPI_STATES = [
    ('draft', '#9ca3af'),
    ('waiting', '#ef4444'),
    ('confirmed', '#0ea5e9'),
    ('assigned', '#f97316'),
    ('done', '#22c55e'),
]


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    def get_view_kpis(self, domain):
        """Return KPI card defs (count by state) aggregated over `domain`.

        `domain` is the view's current search domain, which already carries the
        picking-type filter (incoming for Receipts, outgoing for Deliveries),
        so the same method serves both views.
        """
        domain = domain or []
        groups = self.env['stock.picking']._read_group(
            domain=domain,
            groupby=['state'],
            aggregates=['__count'],
        )
        counts = {state: count for state, count in groups}
        labels = dict(
            self.env['stock.picking']._fields['state']._description_selection(self.env)
        )

        kpis = []
        for state, color in KPI_STATES:
            kpis.append({
                'id': state,
                'label': labels.get(state, state),
                'value': counts.get(state, 0),
                'format': 'integer',
                'color': color,
                'domain': [('state', '=', state)],
            })
        return kpis
