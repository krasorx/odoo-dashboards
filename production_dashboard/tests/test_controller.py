# -*- coding: utf-8 -*-
from odoo.tests.common import tagged
from .common import ProdEstCommon


@tagged('post_install', '-at_install')
class TestRunEstimate(ProdEstCommon):

    def test_run_estimate_miss_then_hit(self):
        out1 = self.Cache.run_estimate('quantity', self.fg.id, self.bom_fg.id, 10, 0, {})
        self.assertFalse(out1['cached'])
        self.assertAlmostEqual(out1['result']['kpis']['total_cost'], 1550.0)
        out2 = self.Cache.run_estimate('quantity', self.fg.id, self.bom_fg.id, 10, 0, {})
        self.assertTrue(out2['cached'])
        self.assertAlmostEqual(out2['result']['kpis']['total_cost'], 1550.0)

    def test_run_estimate_logs_history(self):
        before = self.env['production.estimation.history'].search_count([])
        self.Cache.run_estimate('quantity', self.fg.id, self.bom_fg.id, 7, 0, {})
        after = self.env['production.estimation.history'].search_count([])
        self.assertEqual(after, before + 1)

    def test_run_estimate_cost_mode(self):
        out = self.Cache.run_estimate('cost', self.fg.id, self.bom_fg.id, 0, 1000, {})
        self.assertEqual(out['result']['mode'], 'cost')
        self.assertEqual(out['result']['max_qty'], 6)
