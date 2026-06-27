# -*- coding: utf-8 -*-
from odoo.tests.common import tagged
from .common import ProdEstCommon


@tagged('post_install', '-at_install')
class TestInvalidation(ProdEstCommon):

    def _seed_cache(self):
        key = self.Cache._make_key('quantity', self.fg.id, self.bom_fg.id, 10, {})
        self.Cache.store(key, 'quantity', self.fg.id, self.bom_fg.id,
                         [self.fg.id, self.sa.id, self.c1.id, self.r1.id], {}, {'ok': 1})
        return key

    def test_product_price_change_invalidates(self):
        key = self._seed_cache()
        self.c1.standard_price = 99.0
        self.assertIsNone(self.Cache.get_fresh(key))

    def test_bom_line_change_invalidates_via_reverse(self):
        key = self._seed_cache()
        # cambiar la BOM de SA (subensamble): debe invalidar caché de FG (padre)
        self.bom_sa.bom_line_ids[0].product_qty = 6.0
        self.assertIsNone(self.Cache.get_fresh(key))

    def test_sale_order_line_invalidates(self):
        key = self._seed_cache()
        partner = self.env['res.partner'].create({'name': 'PD Client'})
        so = self.env['sale.order'].create({'partner_id': partner.id})
        self.env['sale.order.line'].create({
            'order_id': so.id, 'product_id': self.c1.id, 'product_uom_qty': 1.0,
        })
        self.assertIsNone(self.Cache.get_fresh(key))

    def test_purchase_order_line_invalidates(self):
        key = self._seed_cache()
        vendor = self.env['res.partner'].create({'name': 'PD Vendor'})
        po = self.env['purchase.order'].create({'partner_id': vendor.id})
        self.env['purchase.order.line'].create({
            'order_id': po.id, 'product_id': self.c1.id,
            'product_qty': 1.0, 'price_unit': 10.0,
        })
        self.assertIsNone(self.Cache.get_fresh(key))

    def test_mo_done_invalidates(self):
        key = self._seed_cache()
        mo = self.env['mrp.production'].create({
            'product_id': self.sa.id, 'product_qty': 1.0, 'bom_id': self.bom_sa.id,
        })
        mo.write({'state': 'done'})
        self.assertIsNone(self.Cache.get_fresh(key))
