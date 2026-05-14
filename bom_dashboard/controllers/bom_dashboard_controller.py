# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request


class BomDashboardController(http.Controller):

    @http.route('/bom/dashboard/boms', type='json', auth='user', methods=['POST'])
    def get_boms(self):
        boms = request.env['mrp.bom'].sudo().search([('active', '=', True)])
        return [{'id': b.id, 'name': b.product_tmpl_id.name} for b in boms]

    @http.route('/bom/dashboard/data', type='json', auth='user', methods=['POST'])
    def get_bom_data(self, bom_id, state_filter=False):
        bom = request.env['mrp.bom'].sudo().browse(int(bom_id))
        if not bom.exists():
            return {'boms': self._get_boms(), 'tree': None}
        tree = self._expand_bom(bom, level=0, state_filter=state_filter,
                                visited=set(), parent_name=None)
        return {'boms': self._get_boms(), 'tree': tree}

    # ── Helpers ────────────────────────────────────────────────────────────────

    def _get_boms(self):
        boms = request.env['mrp.bom'].sudo().search([('active', '=', True)])
        return [{'id': b.id, 'name': b.product_tmpl_id.name} for b in boms]

    def _get_route_type(self, product):
        mfg_route = request.env.ref(
            'mrp.route_warehouse0_manufacture', raise_if_not_found=False)
        if mfg_route and mfg_route in product.route_ids:
            return 'manufacture'
        return 'buy'

    def _get_mos(self, product, state_filter):
        domain = [
            ('product_id', '=', product.id),
            ('state', 'not in', ['done', 'cancel']),
        ]
        if state_filter:
            domain.append(('state', '=', state_filter))
        productions = request.env['mrp.production'].sudo().search(domain)
        return [self._format_mo(p) for p in productions]

    def _format_mo(self, prod):
        user = prod.user_id
        return {
            'id': prod.id,
            'name': prod.name,
            'product_name': prod.product_id.display_name,
            'lot': prod.lot_producing_id.name or '',
            'qty_producing': prod.qty_producing,
            'product_qty': prod.product_qty,
            'state': prod.state,
            'responsible_name': user.name if user else '',
            'responsible_avatar': (
                f'/web/image/res.users/{user.id}/avatar_128' if user else ''
            ),
        }

    def _expand_bom(self, bom, level, state_filter, visited, parent_name):
        """Recursively expand a BOM into a tree node. Max depth: 10."""
        if bom.id in visited or level > 9:
            return None
        visited = visited | {bom.id}

        product = bom.product_id or bom.product_tmpl_id.product_variant_id
        route_type = self._get_route_type(product)
        mos = self._get_mos(product, state_filter) if route_type == 'manufacture' else []

        children = []
        for line in bom.bom_line_ids:
            child_product = line.product_id
            child_route_type = self._get_route_type(child_product)

            child_bom = request.env['mrp.bom'].sudo().search([
                ('product_tmpl_id', '=', child_product.product_tmpl_id.id),
                ('active', '=', True),
            ], limit=1)

            if child_bom and child_bom.id not in visited:
                # Recurse into child BOM
                child_node = self._expand_bom(
                    child_bom, level + 1, state_filter, visited, product.display_name)
                if child_node:
                    # Overlay BOM line qty (bom.product_qty may differ from line qty)
                    child_node['qty'] = line.product_qty
                    child_node['uom'] = line.product_uom_id.name
                    child_node['parent_name'] = product.display_name
                    children.append(child_node)
                    continue

            # Leaf node: no sub-BOM, or already visited (loop guard)
            child_mos = (
                self._get_mos(child_product, state_filter)
                if child_route_type == 'manufacture' else []
            )
            children.append({
                'level': level + 1,
                'product_id': child_product.id,
                'product_name': child_product.display_name,
                'product_ref': child_product.default_code or '',
                'qty': line.product_qty,
                'uom': line.product_uom_id.name,
                'has_bom': bool(child_bom),
                'route_type': child_route_type,
                'parent_name': product.display_name,
                'mos': child_mos,
                'children': [],
            })

        return {
            'level': level,
            'product_id': product.id,
            'product_name': product.display_name,
            'product_ref': product.default_code or '',
            'qty': bom.product_qty,
            'uom': bom.product_uom_id.name,
            'has_bom': True,
            'route_type': route_type,
            'parent_name': parent_name,
            'mos': mos,
            'children': children,
        }
