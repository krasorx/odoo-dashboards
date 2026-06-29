# -*- coding: utf-8 -*-
import math

from odoo import api, models

MAX_BOM_DEPTH = 10


class ProductionEstimationEngine(models.AbstractModel):
    _name = 'production.estimation.engine'
    _description = 'Production Estimation Engine'

    @api.model
    def _bom_find(self, product):
        """Devuelve la BOM normal del producto (recordset, vacío si no hay).
        Compatible con la firma dict de Odoo 16+ y con recordset."""
        Bom = self.env['mrp.bom']
        try:
            res = Bom._bom_find(product)
        except TypeError:
            res = Bom._bom_find(products=product)
        if isinstance(res, dict):
            return res.get(product, Bom)
        return res

    @api.model
    def _unit_cost(self, product, memo=None):
        if memo is None:
            memo = {}
        if product.id in memo:
            return memo[product.id]
        bom = self._bom_find(product)
        if not bom:
            cost = product.standard_price
            memo[product.id] = cost
            return cost
        total = 0.0
        for line in bom.bom_line_ids:
            factor = line.product_qty / (bom.product_qty or 1.0)
            total += factor * self._unit_cost(line.product_id, memo)
        memo[product.id] = total
        return total

    @api.model
    def _route_type(self, product, mfg_route):
        if mfg_route and mfg_route in product.route_ids:
            return 'manufacture'
        if self._bom_find(product):
            return 'manufacture'
        return 'buy'

    @api.model
    def _lead_time(self, product, route):
        if route == 'manufacture':
            bom = self._bom_find(product)
            return bom.produce_delay if bom else 0.0
        seller = product.seller_ids[:1]
        return seller.delay if seller else 0.0

    @api.model
    def _stock_breakdown(self, product):
        """On-hand detail by internal location and lot/serial."""
        Quant = self.env['stock.quant'].sudo()
        quants = Quant.search([
            ('product_id', '=', product.id),
            ('location_id.usage', '=', 'internal'),
            ('quantity', '>', 0),
        ], order='location_id, lot_id')
        tracking = product.tracking or 'none'
        lines = []
        for quant in quants:
            lines.append({
                'lot_name': quant.lot_id.name if quant.lot_id else '',
                'tracking': tracking,
                'qty': quant.quantity,
                'location': quant.location_id.display_name,
                'location_id': quant.location_id.id,
            })
        return lines

    @api.model
    def _build_component_row(
        self, comp, qty_needed, memo, mfg_route, involved,
        depth=0, parent_key='',
    ):
        involved.add(comp.id)
        unit_cost = self._unit_cost(comp, memo)
        total_cost = unit_cost * qty_needed
        available = comp.qty_available
        missing = max(0.0, qty_needed - available)
        real_cost = unit_cost * missing
        route = self._route_type(comp, mfg_route)
        lead = self._lead_time(comp, route)
        child_bom = self._bom_find(comp)
        has_bom = bool(child_bom)
        has_stock = available >= qty_needed
        node_key = f'{parent_key}/{comp.id}' if parent_key else str(comp.id)

        children = []
        if child_bom and depth < MAX_BOM_DEPTH:
            for line in child_bom.bom_line_ids:
                qty_per = line.product_qty / (child_bom.product_qty or 1.0)
                child_qty = qty_per * qty_needed
                child_row, _alerts = self._build_component_row(
                    line.product_id, child_qty, memo, mfg_route, involved,
                    depth=depth + 1, parent_key=node_key,
                )
                children.append(child_row)

        row = {
            'node_key': node_key,
            'product_id': comp.id,
            'name': comp.display_name,
            'ref': comp.default_code or '',
            'qty_needed': qty_needed,
            'unit_cost': unit_cost,
            'total_cost': total_cost,
            'real_cost': real_cost,
            'qty_available': available,
            'qty_missing': missing,
            'has_stock': has_stock,
            'route': route,
            'has_bom': has_bom,
            'lead_time': lead,
            'depth': depth,
            'tracking': comp.tracking or 'none',
            'stock_detail': self._stock_breakdown(comp),
            'children': children,
            'child_count': len(children),
        }
        alerts = []
        if not has_stock:
            alerts.append({
                'type': 'stock',
                'product': comp.display_name,
                'missing': missing,
                'depth': depth,
            })
        return row, alerts

    @api.model
    def _collect_stock_traceability(self, components):
        """Flatten tree into traceability groups for section 2.5."""
        groups = []

        def walk(nodes):
            for node in nodes:
                detail = node.get('stock_detail') or []
                if detail:
                    groups.append({
                        'node_key': node['node_key'],
                        'product_id': node['product_id'],
                        'product': node['name'],
                        'ref': node.get('ref') or '',
                        'tracking': node.get('tracking') or 'none',
                        'depth': node.get('depth', 0),
                        'qty_needed': node.get('qty_needed', 0.0),
                        'lines': detail,
                    })
                walk(node.get('children') or [])

        walk(components)
        return groups

    @api.model
    def _count_tree_nodes(self, components):
        total = 0
        for node in components:
            total += 1
            total += self._count_tree_nodes(node.get('children') or [])
        return total

    @api.model
    def estimate_by_quantity(self, product_id, bom_id, qty, filters=None):
        filters = filters or {}
        product = self.env['product.product'].browse(product_id)
        bom = self.env['mrp.bom'].browse(bom_id) if bom_id else self._bom_find(product)
        qty = float(qty or 0.0)
        memo = {}
        involved = {product.id}
        mfg_route = self.env.ref('mrp.route_warehouse0_manufacture', raise_if_not_found=False)

        components, cost_breakdown, alerts = [], [], []
        in_stock_count = 0
        total_material_cost = 0.0
        total_real_cost = 0.0
        max_child_lead = 0.0
        max_qty_from_stock = 0.0

        if bom:
            stock_limits = []
            for line in bom.bom_line_ids:
                comp = line.product_id
                qty_per_unit = line.product_qty / (bom.product_qty or 1.0)
                qty_needed = qty_per_unit * qty
                row, row_alerts = self._build_component_row(
                    comp, qty_needed, memo, mfg_route, involved, depth=0,
                )
                alerts.extend(row_alerts)
                if row['has_stock']:
                    in_stock_count += 1
                if qty_per_unit > 0:
                    stock_limits.append(row['qty_available'] / qty_per_unit)
                total_material_cost += row['total_cost']
                total_real_cost += row['real_cost']
                max_child_lead = max(max_child_lead, row['lead_time'])
                components.append(row)
                cost_breakdown.append({
                    'name': row['name'],
                    'value': row['total_cost'],
                })
            max_qty_from_stock = (
                math.floor(min(stock_limits)) if stock_limits else 0.0
            )
            unit_cost_total = self._unit_cost(product, memo)
            fg_bom_delay = bom.produce_delay or 0.0
        else:
            unit_cost_total = product.standard_price
            total_material_cost = unit_cost_total * qty
            available = product.qty_available
            missing = max(0.0, qty - available)
            total_real_cost = unit_cost_total * missing
            max_qty_from_stock = math.floor(available) if qty > 0 else 0.0
            fg_bom_delay = 0.0
            alerts.append({'type': 'no_bom', 'product': product.display_name})

        total_lead_time = fg_bom_delay + max_child_lead
        components_count = len(components)
        pct_in_stock = (100.0 * in_stock_count / components_count) if components_count else 100.0
        missing_count = len([c for c in components if not c['has_stock']])

        if filters.get('only_in_stock'):
            components = [c for c in components if c['has_stock']]

        stock_traceability = self._collect_stock_traceability(components)

        return {
            'product': {'id': product.id, 'name': product.display_name,
                        'ref': product.default_code or ''},
            'bom_id': bom.id if bom else False,
            'qty': qty,
            'mode': 'quantity',
            'kpis': {
                'unit_cost': unit_cost_total,
                'total_cost': total_material_cost,
                'real_cost': total_real_cost,
                'real_unit_cost': (
                    total_real_cost / qty if qty > 0 else 0.0
                ),
                'max_qty_from_stock': max_qty_from_stock,
                'total_lead_time': total_lead_time,
                'pct_in_stock': pct_in_stock,
                'components_count': components_count,
                'missing_count': missing_count,
                'tree_nodes_count': self._count_tree_nodes(components),
            },
            'components': components,
            'stock_traceability': stock_traceability,
            'cost_breakdown': cost_breakdown,
            'alerts': alerts,
            'involved_product_ids': sorted(involved),
        }

    @api.model
    def estimate_by_cost(self, product_id, bom_id, budget, filters=None):
        product = self.env['product.product'].browse(product_id)
        bom = self.env['mrp.bom'].browse(bom_id) if bom_id else self._bom_find(product)
        budget = float(budget or 0.0)
        memo = {}
        unit_cost = self._unit_cost(product, memo) if bom else product.standard_price
        max_qty = int(math.floor(budget / unit_cost)) if unit_cost > 0 else 0
        result = self.estimate_by_quantity(product_id, bom.id if bom else False, max_qty, filters)
        result['mode'] = 'cost'
        result['budget'] = budget
        result['max_qty'] = max_qty
        result['remaining'] = budget - result['kpis']['total_cost']
        return result

    @api.model
    def bom_detail(self, bom_id, qty=1.0):
        bom = self.env['mrp.bom'].browse(bom_id)
        if not bom.exists():
            return {}
        product = bom.product_id or bom.product_tmpl_id.product_variant_id
        return self.estimate_by_quantity(product.id, bom.id, qty, {})