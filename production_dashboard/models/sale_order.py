# -*- coding: utf-8 -*-
from odoo import api, models


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    def _pd_invalidate(self):
        products = self.mapped('product_id').ids
        self.env['production.estimation.cache'].invalidate_for_products(products)

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
