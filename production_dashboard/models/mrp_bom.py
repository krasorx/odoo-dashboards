# -*- coding: utf-8 -*-
from odoo import api, models


class MrpBom(models.Model):
    _inherit = 'mrp.bom'

    def _pd_invalidate(self):
        products = self.mapped('product_tmpl_id.product_variant_ids').ids
        products += self.mapped('bom_line_ids.product_id').ids
        Cache = self.env['production.estimation.cache']
        Cache.invalidate_for_products(Cache._reverse_bom_products(products))

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
        products = self.mapped('product_tmpl_id.product_variant_ids').ids
        products += self.mapped('bom_line_ids.product_id').ids
        Cache = self.env['production.estimation.cache']
        affected = Cache._reverse_bom_products(products)
        res = super().unlink()
        Cache.invalidate_for_products(affected)
        return res


class MrpBomLine(models.Model):
    _inherit = 'mrp.bom.line'

    def _pd_invalidate(self):
        products = self.mapped('product_id').ids
        products += self.mapped('bom_id.product_tmpl_id.product_variant_ids').ids
        Cache = self.env['production.estimation.cache']
        Cache.invalidate_for_products(Cache._reverse_bom_products(products))

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
        products += self.mapped('bom_id.product_tmpl_id.product_variant_ids').ids
        Cache = self.env['production.estimation.cache']
        affected = Cache._reverse_bom_products(products)
        res = super().unlink()
        Cache.invalidate_for_products(affected)
        return res
