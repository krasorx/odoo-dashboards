# -*- coding: utf-8 -*-
from odoo import models


class MrpProduction(models.Model):
    _inherit = 'mrp.production'

    def _post_inventory(self, cancel_backorder=False):
        """Invalidate when an MO posts its inventory (i.e. actually produces).

        ``mrp.production.state`` is a computed/readonly field, so the old
        ``write({'state': 'done'})`` hook never fired — that was the root of
        the "still no stock after manufacturing" bug. ``_post_inventory`` is
        the method that moves the finished goods into stock and consumes the
        components, so it's the right place to refresh the dashboard cache for
        the produced product and its raw materials. (The stock.quant hook also
        covers this; this keeps the intent explicit and resilient.)
        """
        res = super()._post_inventory(cancel_backorder=cancel_backorder)
        products = list(self.mapped('product_id').ids)
        products += self.mapped('move_raw_ids.product_id').ids
        self.env['production.estimation.cache'].invalidate_for_products(products)
        return res
