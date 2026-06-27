# -*- coding: utf-8 -*-
from odoo import api, models


class StockMove(models.Model):
    _inherit = 'stock.move'

    def write(self, vals):
        res = super().write(vals)
        if vals.get('state') == 'done':
            self.env['production.estimation.cache'].invalidate_for_products(
                self.mapped('product_id').ids)
        return res


class StockLot(models.Model):
    _inherit = 'stock.lot'

    def _pd_invalidate(self):
        self.env['production.estimation.cache'].invalidate_for_products(
            self.mapped('product_id').ids)

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        records._pd_invalidate()
        return records

    def write(self, vals):
        res = super().write(vals)
        self._pd_invalidate()
        return res

    def unlink(self):
        products = self.mapped('product_id').ids
        res = super().unlink()
        self.env['production.estimation.cache'].invalidate_for_products(products)
        return res
