# -*- coding: utf-8 -*-
from datetime import timedelta
from odoo import fields
from odoo.tests.common import tagged
from .common import ProdEstCommon


@tagged('post_install', '-at_install')
class TestCache(ProdEstCommon):

    def test_make_key_is_deterministic_and_order_independent(self):
        k1 = self.Cache._make_key('quantity', self.fg.id, self.bom_fg.id, 10, {'a': 1, 'b': 2})
        k2 = self.Cache._make_key('quantity', self.fg.id, self.bom_fg.id, 10, {'b': 2, 'a': 1})
        k3 = self.Cache._make_key('quantity', self.fg.id, self.bom_fg.id, 11, {'a': 1, 'b': 2})
        self.assertEqual(k1, k2)
        self.assertNotEqual(k1, k3)
        self.assertEqual(len(k1), 64)

    def test_store_and_get_fresh(self):
        key = self.Cache._make_key('quantity', self.fg.id, self.bom_fg.id, 5, {})
        rec = self.Cache.store(key, 'quantity', self.fg.id, self.bom_fg.id,
                               [self.fg.id, self.sa.id, self.c1.id], {}, {'ok': True})
        self.assertTrue(rec.exists())
        fresh = self.Cache.get_fresh(key)
        self.assertEqual(fresh, rec)

    def test_get_fresh_returns_none_when_expired(self):
        key = self.Cache._make_key('quantity', self.fg.id, self.bom_fg.id, 5, {})
        rec = self.Cache.store(key, 'quantity', self.fg.id, self.bom_fg.id, [self.fg.id], {}, {'ok': 1})
        ttl = self.Cache._ttl_seconds()
        past = fields.Datetime.now() - timedelta(seconds=ttl + 60)
        # write_date es auto-gestionado por el ORM; forzarlo por SQL para simular expiración
        self.env.cr.execute(
            "UPDATE production_estimation_cache SET write_date = %s WHERE id = %s",
            (past, rec.id))
        rec.invalidate_recordset(['write_date'])
        self.assertIsNone(self.Cache.get_fresh(key))

    def test_store_upserts_on_same_key(self):
        key = self.Cache._make_key('quantity', self.fg.id, self.bom_fg.id, 5, {})
        self.Cache.store(key, 'quantity', self.fg.id, self.bom_fg.id, [self.fg.id], {}, {'v': 1})
        self.Cache.store(key, 'quantity', self.fg.id, self.bom_fg.id, [self.fg.id], {}, {'v': 2})
        recs = self.Cache.search([('cache_key', '=', key)])
        self.assertEqual(len(recs), 1)

    def test_invalidate_for_products(self):
        key = self.Cache._make_key('quantity', self.fg.id, self.bom_fg.id, 5, {})
        self.Cache.store(key, 'quantity', self.fg.id, self.bom_fg.id,
                         [self.fg.id, self.sa.id, self.c1.id], {}, {'ok': 1})
        n = self.Cache.invalidate_for_products([self.c1.id])
        self.assertEqual(n, 1)
        self.assertIsNone(self.Cache.get_fresh(key))

    def test_reverse_bom_products_finds_parents(self):
        affected = self.Cache._reverse_bom_products([self.r1.id])
        # R1 -> SA -> FG
        self.assertIn(self.sa.id, affected)
        self.assertIn(self.fg.id, affected)
