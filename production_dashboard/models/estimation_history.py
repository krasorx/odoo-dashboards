# -*- coding: utf-8 -*-
import json

from odoo import api, fields, models


class ProductionEstimationHistory(models.Model):
    _name = 'production.estimation.history'
    _description = 'Production Estimation History'
    _order = 'create_date desc, id desc'

    user_id = fields.Many2one('res.users', default=lambda self: self.env.user, index=True)
    product_id = fields.Many2one('product.product', index=True, ondelete='cascade')
    bom_id = fields.Many2one('mrp.bom', ondelete='set null')
    mode = fields.Selection([('quantity', 'By Quantity'), ('cost', 'By Cost')])
    qty = fields.Float()
    budget = fields.Float()
    unit_cost = fields.Float()
    total_cost = fields.Float()
    total_lead_time = fields.Float()
    pct_in_stock = fields.Float()
    filters_json = fields.Text()

    @api.model
    def log_run(self, mode, product_id, bom_id, amount, kpis, filters):
        kpis = kpis or {}
        return self.create({
            'mode': mode,
            'product_id': product_id or False,
            'bom_id': bom_id or False,
            'qty': amount if mode == 'quantity' else 0.0,
            'budget': kpis.get('budget', amount if mode == 'cost' else 0.0),
            'unit_cost': kpis.get('unit_cost', 0.0),
            'total_cost': kpis.get('total_cost', 0.0),
            'total_lead_time': kpis.get('total_lead_time', 0.0),
            'pct_in_stock': kpis.get('pct_in_stock', 0.0),
            'filters_json': json.dumps(filters or {}, default=str),
        })

    @api.model
    def recent(self, limit=20):
        records = self.search([], limit=limit)
        return [{
            'id': r.id,
            'user': r.user_id.name,
            'product': r.product_id.display_name,
            'product_id': r.product_id.id,
            'bom_id': r.bom_id.id,
            'mode': r.mode,
            'qty': r.qty,
            'budget': r.budget,
            'unit_cost': r.unit_cost,
            'total_cost': r.total_cost,
            'total_lead_time': r.total_lead_time,
            'pct_in_stock': r.pct_in_stock,
            'date': fields.Datetime.to_string(r.create_date),
        } for r in records]
