# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request


class EstimationController(http.Controller):

    @http.route('/production/estimation/products', type='jsonrpc', auth='user', methods=['POST'])
    def products(self):
        boms = request.env['mrp.bom'].sudo().search([('active', '=', True)])
        seen, out = set(), []
        for bom in boms:
            product = bom.product_id or bom.product_tmpl_id.product_variant_id
            if product.id in seen:
                continue
            seen.add(product.id)
            out.append({
                'id': product.id,
                'name': product.display_name,
                'ref': product.default_code or '',
                'bom_id': bom.id,
            })
        return out

    @http.route('/production/estimation/bom_variants', type='jsonrpc', auth='user', methods=['POST'])
    def bom_variants(self, product_id):
        product = request.env['product.product'].sudo().browse(int(product_id))
        boms = request.env['mrp.bom'].sudo().search([
            ('product_tmpl_id', '=', product.product_tmpl_id.id),
            ('active', '=', True),
        ])
        return [{'id': b.id, 'name': b.display_name or ('BOM %s' % b.id)} for b in boms]

    @http.route('/production/estimation/estimate', type='jsonrpc', auth='user', methods=['POST'])
    def estimate(self, mode, product_id, bom_id=False, qty=0, budget=0, filters=None):
        return request.env['production.estimation.cache'].sudo().run_estimate(
            mode, int(product_id), int(bom_id) if bom_id else False,
            float(qty or 0), float(budget or 0), filters or {})

    @http.route('/production/estimation/history', type='jsonrpc', auth='user', methods=['POST'])
    def history(self, limit=20):
        return request.env['production.estimation.history'].sudo().recent(limit=int(limit))

    @http.route('/production/estimation/bom_detail', type='jsonrpc', auth='user', methods=['POST'])
    def bom_detail(self, bom_id, qty=1.0):
        return request.env['production.estimation.engine'].sudo().bom_detail(
            int(bom_id), float(qty or 1.0))

    # ── AI assistant (only meaningful when custom_agent is installed) ────────
    @http.route('/production/estimation/ai_status', type='jsonrpc', auth='user', methods=['POST'])
    def ai_status(self):
        return request.env['production.estimation.ai'].sudo().status()

    @http.route('/production/estimation/ai_analyze', type='jsonrpc', auth='user', methods=['POST'])
    def ai_analyze(self, mode, product_id, bom_id=False, qty=0, budget=0, filters=None):
        return request.env['production.estimation.ai'].sudo().analyze(
            mode, int(product_id), int(bom_id) if bom_id else False,
            float(qty or 0), float(budget or 0), filters or {})

    @http.route('/production/estimation/ai_execute', type='jsonrpc', auth='user', methods=['POST'])
    def ai_execute(self, kind, mode, product_id, bom_id=False, qty=0, budget=0, filters=None):
        return request.env['production.estimation.ai'].sudo().execute(
            kind, mode, int(product_id), int(bom_id) if bom_id else False,
            float(qty or 0), float(budget or 0), filters or {})
