# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request

MAX_BOM_DEPTH = 10


class BomDashboardController(http.Controller):

    @http.route('/bom/dashboard/boms', type='json', auth='user', methods=['POST'])
    def get_boms(self):
        return self._get_boms()

    @http.route('/bom/dashboard/data', type='json', auth='user', methods=['POST'])
    def get_bom_data(self, bom_id, state_filter=False):
        bom = request.env['mrp.bom'].sudo().browse(int(bom_id))
        if not bom.exists():
            return {'boms': self._get_boms(), 'tree': None}

        # Cache manufacture route once for the entire request
        mfg_route = request.env.ref(
            'mrp.route_warehouse0_manufacture', raise_if_not_found=False)

        # Collect all BOM IDs reachable from this root (to batch-fetch data)
        all_bom_ids, all_product_tmpl_ids, all_product_ids = set(), set(), set()
        self._collect_ids(bom, all_bom_ids, all_product_tmpl_ids, all_product_ids, set())

        # Batch: child BOM lookup indexed by product_tmpl_id
        child_boms_by_tmpl = {}
        child_boms = request.env['mrp.bom'].sudo().search([
            ('product_tmpl_id', 'in', list(all_product_tmpl_ids)),
            ('active', '=', True),
        ])
        for cb in child_boms:
            tmpl_id = cb.product_tmpl_id.id
            # Keep only the first BOM per template (same limit=1 logic)
            if tmpl_id not in child_boms_by_tmpl:
                child_boms_by_tmpl[tmpl_id] = cb

        # Batch: active MOs indexed by product_id
        mo_domain = [
            ('product_id', 'in', list(all_product_ids)),
            ('state', 'not in', ['done', 'cancel']),
        ]
        if state_filter:
            mo_domain.append(('state', '=', state_filter))
        all_mos = request.env['mrp.production'].sudo().search(mo_domain)
        mos_by_product = {}
        for mo in all_mos:
            mos_by_product.setdefault(mo.product_id.id, []).append(self._format_mo(mo))

        tree = self._expand_bom(
            bom, level=0, visited=set(),
            parent_name=None,
            mfg_route=mfg_route,
            child_boms_by_tmpl=child_boms_by_tmpl,
            mos_by_product=mos_by_product,
        )
        return {'boms': self._get_boms(), 'tree': tree}

    # ── Helpers ────────────────────────────────────────────────────────────────

    def _get_boms(self):
        boms = request.env['mrp.bom'].sudo().search([('active', '=', True)])
        return [{'id': b.id, 'name': b.product_tmpl_id.name} for b in boms]

    def _collect_ids(self, bom, bom_ids, tmpl_ids, product_ids, visited):
        """Walk the BOM tree to collect all IDs for batch fetching."""
        if bom.id in visited or len(visited) > MAX_BOM_DEPTH * 10:
            return
        visited = visited | {bom.id}
        bom_ids.add(bom.id)
        product = bom.product_id or bom.product_tmpl_id.product_variant_id
        tmpl_ids.add(bom.product_tmpl_id.id)
        product_ids.add(product.id)
        for line in bom.bom_line_ids:
            lp = line.product_id
            tmpl_ids.add(lp.product_tmpl_id.id)
            product_ids.add(lp.id)
            # Recurse into child BOMs already loaded (pre-fetch not yet done,
            # so we search here only to discover the tree shape)
            child_bom = request.env['mrp.bom'].sudo().search([
                ('product_tmpl_id', '=', lp.product_tmpl_id.id),
                ('active', '=', True),
            ], limit=1)
            if child_bom and child_bom.id not in visited:
                self._collect_ids(child_bom, bom_ids, tmpl_ids, product_ids, visited)

    def _get_route_type(self, product, mfg_route):
        if mfg_route and mfg_route in product.route_ids:
            return 'manufacture'
        return 'buy'

    def _format_mo(self, prod):
        user = prod.user_id
        return {
            'id': prod.id,
            'name': prod.name,
            'product_name': prod.product_id.display_name,
            'lot': prod.lot_producing_id.name if prod.lot_producing_id else '',
            'qty_producing': prod.qty_producing,
            'product_qty': prod.product_qty,
            'state': prod.state,
            'responsible_name': user.name if user else '',
            'responsible_avatar': (
                f'/web/image/res.users/{user.id}/avatar_128' if user else ''
            ),
        }

    def _expand_bom(self, bom, level, visited, parent_name,
                    mfg_route, child_boms_by_tmpl, mos_by_product):
        """Recursively build tree node using pre-fetched data maps."""
        if bom.id in visited or level > MAX_BOM_DEPTH - 1:
            return None
        visited = visited | {bom.id}

        product = bom.product_id or bom.product_tmpl_id.product_variant_id
        route_type = self._get_route_type(product, mfg_route)
        mos = mos_by_product.get(product.id, []) if route_type == 'manufacture' else []

        children = []
        for line in bom.bom_line_ids:
            child_product = line.product_id
            child_route_type = self._get_route_type(child_product, mfg_route)
            child_bom = child_boms_by_tmpl.get(child_product.product_tmpl_id.id)

            if child_bom and child_bom.id not in visited:
                child_node = self._expand_bom(
                    child_bom, level + 1, visited, product.display_name,
                    mfg_route, child_boms_by_tmpl, mos_by_product)
                if child_node:
                    child_node['qty'] = line.product_qty
                    child_node['uom'] = line.product_uom_id.name
                    child_node['parent_name'] = product.display_name
                    children.append(child_node)
                    continue

            # Leaf node
            child_mos = (
                mos_by_product.get(child_product.id, [])
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
