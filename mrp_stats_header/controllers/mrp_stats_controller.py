# -*- coding: utf-8 -*-
from datetime import datetime, timedelta
from odoo import http
from odoo.http import request

STATES = ['draft', 'confirmed', 'progress', 'to_close', 'waiting', 'done']


class MrpStatsController(http.Controller):

    @http.route('/mrp/stats/counts', type='json', auth='user', methods=['POST'])
    def get_counts(self, scope='week'):
        domain = [('state', 'not in', ['cancel'])]

        if scope == 'week':
            today = datetime.utcnow()
            monday = today - timedelta(days=today.weekday())
            monday = monday.replace(hour=0, minute=0, second=0, microsecond=0)
            sunday = monday + timedelta(days=6)
            sunday = sunday.replace(hour=23, minute=59, second=59)
            domain += [
                ('date_start', '>=', monday.strftime('%Y-%m-%d %H:%M:%S')),
                ('date_start', '<=', sunday.strftime('%Y-%m-%d %H:%M:%S')),
            ]

        groups = request.env['mrp.production'].sudo().read_group(
            domain=domain,
            fields=['state'],
            groupby=['state'],
        )

        result = {s: 0 for s in STATES}
        for g in groups:
            state = g.get('state')
            if state in result:
                result[state] = g.get('state_count', 0)
        return result
