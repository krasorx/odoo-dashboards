# -*- coding: utf-8 -*-
from odoo import models

PD_COST_FIELDS = {'standard_price', 'list_price'}


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    def write(self, vals):
        res = super().write(vals)
        if PD_COST_FIELDS & set(vals.keys()):
            self.env['production.estimation.cache'].invalidate_for_products(
                self.mapped('product_variant_ids').ids)
        return res


class ProductProduct(models.Model):
    _inherit = 'product.product'

    def write(self, vals):
        res = super().write(vals)
        if PD_COST_FIELDS & set(vals.keys()):
            self.env['production.estimation.cache'].invalidate_for_products(self.ids)
        return res
