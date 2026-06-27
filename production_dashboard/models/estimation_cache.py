# -*- coding: utf-8 -*-
import hashlib
import json
from datetime import timedelta

from odoo import api, fields, models


class ProductionEstimationCache(models.Model):
    _name = 'production.estimation.cache'
    _description = 'Production Estimation Cache'
    _rec_name = 'cache_key'

    cache_key = fields.Char(required=True, index=True)
    mode = fields.Selection([('quantity', 'By Quantity'), ('cost', 'By Cost')])
    product_id = fields.Many2one('product.product', index=True, ondelete='cascade')
    bom_id = fields.Many2one('mrp.bom', index=True, ondelete='cascade')
    involved_product_ids = fields.Many2many(
        'product.product', 'prod_est_cache_product_rel', 'cache_id', 'product_id')
    params_json = fields.Text()
    result_json = fields.Text()

    _sql_constraints = [
        ('cache_key_uniq', 'unique(cache_key)', 'Cache key must be unique.'),
    ]

    @api.model
    def _ttl_seconds(self):
        val = self.env['ir.config_parameter'].sudo().get_param(
            'production_dashboard.cache_ttl', '3600')
        try:
            return int(val)
        except (TypeError, ValueError):
            return 3600

    @api.model
    def _make_key(self, mode, product_id, bom_id, amount, filters):
        payload = {
            'mode': mode,
            'product_id': product_id or False,
            'bom_id': bom_id or False,
            'amount': round(float(amount or 0.0), 4),
            'filters': filters or {},
        }
        raw = json.dumps(payload, sort_keys=True, default=str)
        return hashlib.sha256(raw.encode('utf-8')).hexdigest()

    @api.model
    def get_fresh(self, key):
        rec = self.search([('cache_key', '=', key)], limit=1)
        if not rec:
            return None
        age = (fields.Datetime.now() - rec.write_date).total_seconds()
        if age > self._ttl_seconds():
            return None
        return rec

    @api.model
    def store(self, key, mode, product_id, bom_id, involved_ids, params, result):
        vals = {
            'cache_key': key,
            'mode': mode,
            'product_id': product_id or False,
            'bom_id': bom_id or False,
            'involved_product_ids': [(6, 0, [p for p in set(involved_ids or []) if p])],
            'params_json': json.dumps(params or {}, default=str),
            'result_json': json.dumps(result or {}, default=str),
        }
        existing = self.search([('cache_key', '=', key)], limit=1)
        if existing:
            existing.write(vals)
            return existing
        return self.create(vals)

    @api.model
    def run_estimate(self, mode, product_id, bom_id, qty, budget, filters):
        filters = filters or {}
        amount = qty if mode == 'quantity' else budget
        key = self._make_key(mode, product_id, bom_id, amount, filters)
        hit = self.get_fresh(key)
        if hit:
            return {'cached': True, 'result': json.loads(hit.result_json)}
        Engine = self.env['production.estimation.engine']
        if mode == 'cost':
            result = Engine.estimate_by_cost(product_id, bom_id, budget, filters)
        else:
            result = Engine.estimate_by_quantity(product_id, bom_id, qty, filters)
        self.store(key, mode, product_id, bom_id,
                   result.get('involved_product_ids', []), filters, result)
        self.env['production.estimation.history'].log_run(
            mode, product_id, bom_id, amount, result.get('kpis', {}), filters)
        return {'cached': False, 'result': result}

    @api.model
    def invalidate_for_products(self, product_ids):
        product_ids = [p for p in set(product_ids or []) if p]
        if not product_ids:
            return 0
        recs = self.search([
            '|',
            ('involved_product_ids', 'in', product_ids),
            ('product_id', 'in', product_ids),
        ])
        count = len(recs)
        recs.unlink()
        return count

    @api.model
    def _reverse_bom_products(self, product_ids):
        """Devuelve los product_ids más todos los productos padre cuya BOM
        (anidada) los usa como componente. Iterativo hasta punto fijo."""
        result = set(p for p in (product_ids or []) if p)
        frontier = set(result)
        seen = set()
        BomLine = self.env['mrp.bom.line']
        while frontier:
            lines = BomLine.search([('product_id', 'in', list(frontier))])
            parents = set()
            for line in lines:
                for variant in line.bom_id.product_tmpl_id.product_variant_ids:
                    if variant.id not in result:
                        parents.add(variant.id)
            seen |= frontier
            result |= parents
            frontier = parents - seen
        return list(result)

    @api.model
    def _gc_expired(self):
        ttl = self._ttl_seconds()
        threshold = fields.Datetime.now() - timedelta(seconds=ttl)
        self.search([('write_date', '<', threshold)]).unlink()
