# -*- coding: utf-8 -*-
from odoo.tests.common import tagged
from .common import ProdEstCommon


@tagged('post_install', '-at_install')
class TestHistory(ProdEstCommon):

    def setUp(self):
        super().setUp()
        self.History = self.env['production.estimation.history']

    def test_log_and_recent(self):
        kpis = {'unit_cost': 155.0, 'total_cost': 1550.0,
                'total_lead_time': 5.0, 'pct_in_stock': 50.0}
        rec = self.History.log_run('quantity', self.fg.id, self.bom_fg.id, 10, kpis, {})
        self.assertTrue(rec.exists())
        recent = self.History.recent(limit=5)
        self.assertTrue(any(r['id'] == rec.id for r in recent))
        first = recent[0]
        self.assertEqual(first['mode'], 'quantity')
        self.assertAlmostEqual(first['total_cost'], 1550.0)

    def test_recent_is_global_and_ordered(self):
        kpis = {'unit_cost': 1, 'total_cost': 1, 'total_lead_time': 1, 'pct_in_stock': 1}
        self.History.log_run('quantity', self.fg.id, self.bom_fg.id, 1, kpis, {})
        self.History.log_run('cost', self.fg.id, self.bom_fg.id, 0, dict(kpis, budget=500), {})
        recent = self.History.recent(limit=2)
        self.assertEqual(len(recent), 2)
        # más reciente primero
        self.assertEqual(recent[0]['mode'], 'cost')
