# -*- coding: utf-8 -*-
from odoo.tests.common import tagged
from .common import ProdEstCommon


@tagged('post_install', '-at_install')
class TestEngine(ProdEstCommon):

    def setUp(self):
        super().setUp()
        self.Engine = self.env['production.estimation.engine']

    def test_unit_cost_recursive(self):
        # SA = 4 x R1(10) = 40 ; FG = 2 x SA(40) + 3 x C1(25) = 80 + 75 = 155
        self.assertAlmostEqual(self.Engine._unit_cost(self.sa), 40.0)
        self.assertAlmostEqual(self.Engine._unit_cost(self.fg), 155.0)

    def test_estimate_by_quantity_totals(self):
        res = self.Engine.estimate_by_quantity(self.fg.id, self.bom_fg.id, 10)
        self.assertAlmostEqual(res['kpis']['unit_cost'], 155.0)
        self.assertAlmostEqual(res['kpis']['total_cost'], 1550.0)
        self.assertEqual(res['kpis']['components_count'], 2)
        names = {c['name'] for c in res['components']}
        self.assertEqual(names, {self.sa.display_name, self.c1.display_name})

    def test_estimate_by_quantity_component_quantities(self):
        res = self.Engine.estimate_by_quantity(self.fg.id, self.bom_fg.id, 10)
        by_id = {c['product_id']: c for c in res['components']}
        self.assertAlmostEqual(by_id[self.sa.id]['qty_needed'], 20.0)
        self.assertAlmostEqual(by_id[self.c1.id]['qty_needed'], 30.0)
        self.assertAlmostEqual(by_id[self.sa.id]['total_cost'], 800.0)
        self.assertAlmostEqual(by_id[self.c1.id]['total_cost'], 750.0)

    def test_estimate_includes_involved_products(self):
        res = self.Engine.estimate_by_quantity(self.fg.id, self.bom_fg.id, 1)
        self.assertIn(self.fg.id, res['involved_product_ids'])
        self.assertIn(self.sa.id, res['involved_product_ids'])
        self.assertIn(self.c1.id, res['involved_product_ids'])

    def test_estimate_by_cost_max_qty(self):
        # unit_cost FG = 155 ; budget 1000 -> floor(1000/155) = 6
        res = self.Engine.estimate_by_cost(self.fg.id, self.bom_fg.id, 1000.0)
        self.assertEqual(res['mode'], 'cost')
        self.assertEqual(res['max_qty'], 6)
        self.assertAlmostEqual(res['kpis']['total_cost'], 930.0)
        self.assertAlmostEqual(res['remaining'], 70.0)

    def test_bom_detail(self):
        res = self.Engine.bom_detail(self.bom_fg.id, 2)
        self.assertEqual(res['bom_id'], self.bom_fg.id)
        self.assertAlmostEqual(res['kpis']['total_cost'], 310.0)

    def test_lead_time_uses_bom_produce_delay(self):
        res = self.Engine.estimate_by_quantity(self.fg.id, self.bom_fg.id, 1)
        # FG bom delay (3) + max child lead (SA manufacture bom delay 2) = 5
        self.assertAlmostEqual(res['kpis']['total_lead_time'], 5.0)

    def test_real_cost_counts_only_missing_qty(self):
        warehouse = self.env['stock.warehouse'].search(
            [('company_id', '=', self.env.company.id)], limit=1,
        )
        location = warehouse.lot_stock_id
        Quant = self.env['stock.quant']
        Quant._update_available_quantity(self.c1, location, 30.0)
        Quant._update_available_quantity(self.sa, location, 0.0)

        res = self.Engine.estimate_by_quantity(self.fg.id, self.bom_fg.id, 10)
        by_id = {c['product_id']: c for c in res['components']}

        self.assertAlmostEqual(res['kpis']['total_cost'], 1550.0)
        self.assertAlmostEqual(by_id[self.c1.id]['real_cost'], 0.0)
        self.assertAlmostEqual(by_id[self.sa.id]['real_cost'], 800.0)
        self.assertAlmostEqual(res['kpis']['real_cost'], 800.0)
        self.assertAlmostEqual(res['kpis']['real_unit_cost'], 80.0)

    def test_multilevel_bom_children(self):
        res = self.Engine.estimate_by_quantity(self.fg.id, self.bom_fg.id, 1)
        sa = next(c for c in res['components'] if c['product_id'] == self.sa.id)
        self.assertTrue(sa['has_bom'])
        self.assertEqual(sa['child_count'], 1)
        self.assertEqual(sa['children'][0]['product_id'], self.r1.id)
        self.assertAlmostEqual(sa['children'][0]['qty_needed'], 8.0)
        self.assertEqual(res['kpis']['components_count'], 2)
        self.assertEqual(res['kpis']['tree_nodes_count'], 3)

    def test_stock_breakdown_and_traceability(self):
        warehouse = self.env['stock.warehouse'].search(
            [('company_id', '=', self.env.company.id)], limit=1,
        )
        lot = self.env['stock.lot'].create({
            'name': 'LOT-TEST-R1',
            'product_id': self.r1.id,
        })
        self.env['stock.quant'].sudo().with_context(inventory_mode=True).create({
            'product_id': self.r1.id,
            'location_id': warehouse.lot_stock_id.id,
            'lot_id': lot.id,
            'inventory_quantity': 5.0,
        }).action_apply_inventory()

        res = self.Engine.estimate_by_quantity(self.fg.id, self.bom_fg.id, 1)
        sa = next(c for c in res['components'] if c['product_id'] == self.sa.id)
        r1 = sa['children'][0]
        self.assertTrue(r1['stock_detail'])
        self.assertEqual(r1['stock_detail'][0]['lot_name'], 'LOT-TEST-R1')
        self.assertIn('Stock', r1['stock_detail'][0]['location'])
        trace = {t['product_id']: t for t in res['stock_traceability']}
        self.assertIn(self.r1.id, trace)

    def test_max_qty_from_stock_without_purchase(self):
        warehouse = self.env['stock.warehouse'].search(
            [('company_id', '=', self.env.company.id)], limit=1,
        )
        location = warehouse.lot_stock_id
        Quant = self.env['stock.quant']
        Quant._update_available_quantity(self.c1, location, 30.0)
        Quant._update_available_quantity(self.sa, location, 20.0)

        res = self.Engine.estimate_by_quantity(self.fg.id, self.bom_fg.id, 10)
        self.assertEqual(res['kpis']['max_qty_from_stock'], 10)
        self.assertAlmostEqual(res['kpis']['real_cost'], 0.0)
