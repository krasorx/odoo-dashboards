# -*- coding: utf-8 -*-
from odoo import models


class MrpProduction(models.Model):
    _inherit = 'mrp.production'

    def write(self, vals):
        res = super().write(vals)
        if vals.get('state') == 'done':
            products = list(self.mapped('product_id').ids)
            products += self.mapped('move_raw_ids.product_id').ids
            self.env['production.estimation.cache'].invalidate_for_products(products)
        return res
