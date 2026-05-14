# -*- coding: utf-8 -*-
from datetime import datetime, timedelta
from odoo import http
from odoo.http import request


class MrpDashboardController(http.Controller):

    @http.route('/mrp/dashboard/weekly_orders', type='json', auth='user', methods=['POST'])
    def weekly_orders(self, week_start, team_id=False):
        week_start_dt = datetime.strptime(week_start, '%Y-%m-%d')
        week_end_dt = week_start_dt + timedelta(days=7)

        domain = [
            ('date_start', '>=', week_start_dt.strftime('%Y-%m-%d 00:00:00')),
            ('date_start', '<', week_end_dt.strftime('%Y-%m-%d 00:00:00')),
        ]

        if team_id:
            team = request.env['mrp.team'].sudo().browse(int(team_id))
            user_ids = team.member_ids.mapped('user_id').ids
            if not user_ids:
                return {
                    'orders': self._empty_week(week_start_dt),
                    'teams': self._get_teams(),
                }
            domain.append(('user_id', 'in', user_ids))

        productions = request.env['mrp.production'].sudo().search(
            domain, order='date_start asc'
        )

        orders = self._empty_week(week_start_dt)
        for prod in productions:
            if not prod.date_start:
                continue
            day_key = prod.date_start.strftime('%Y-%m-%d')
            if day_key not in orders:
                continue

            user = prod.user_id
            avatar_url = (
                f'/web/image/res.users/{user.id}/avatar_128' if user else ''
            )

            components = []
            for move in prod.move_raw_ids[:3]:
                comp = move.product_id.display_name or ''
                lot = (
                    move.move_line_ids[:1].lot_id.name
                    if move.move_line_ids
                    else ''
                )
                if lot:
                    comp += f' [{lot}]'
                components.append(comp)

            orders[day_key].append({
                'id': prod.id,
                'name': prod.name,
                'product_name': prod.product_id.display_name or '',
                'lot': prod.lot_producing_id.name or '',
                'qty_producing': prod.qty_producing,
                'product_qty': prod.product_qty,
                'state': prod.state,
                'responsible_name': user.name if user else '',
                'responsible_avatar': avatar_url,
                'components': components,
            })

        return {'orders': orders, 'teams': self._get_teams()}

    def _empty_week(self, week_start_dt):
        return {
            (week_start_dt + timedelta(days=i)).strftime('%Y-%m-%d'): []
            for i in range(7)
        }

    def _get_teams(self):
        teams = request.env['mrp.team'].sudo().search([])
        return [{'id': t.id, 'name': t.name} for t in teams]
