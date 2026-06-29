# -*- coding: utf-8 -*-
from odoo.tests.common import tagged
from .common import ProdEstCommon


@tagged('post_install', '-at_install')
class TestDemoStock(ProdEstCommon):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Demo = cls.env['production.estimation.demo']

    def test_load_serial_and_lot_stock(self):
        Product = self.env['product.product']
        serial_prod = Product.create({
            'name': 'PD Test Serial',
            'default_code': 'PD-TEST-SER01',
            'is_storable': True,
            'tracking': 'serial',
            'standard_price': 10.0,
        })
        lot_prod = Product.create({
            'name': 'PD Test Lot',
            'default_code': 'PD-TEST-LOT01',
            'is_storable': True,
            'tracking': 'lot',
            'standard_price': 5.0,
        })
        location = self.Demo._stock_location()
        self.assertTrue(location)

        self.Demo._set_inventory(
            serial_prod, location, 1.0,
            lot=self.Demo._get_or_create_lot(serial_prod, 'SN-TEST-001'),
        )
        self.Demo._set_inventory(
            serial_prod, location, 1.0,
            lot=self.Demo._get_or_create_lot(serial_prod, 'SN-TEST-002'),
        )
        self.Demo._set_inventory(
            lot_prod, location, 12.0,
            lot=self.Demo._get_or_create_lot(lot_prod, 'LOT-TEST-A'),
        )

        serial_prod.invalidate_recordset(['qty_available'])
        lot_prod.invalidate_recordset(['qty_available'])
        self.assertAlmostEqual(serial_prod.qty_available, 2.0)
        self.assertAlmostEqual(lot_prod.qty_available, 12.0)

        lots = self.env['stock.lot'].search([
            ('product_id', 'in', [serial_prod.id, lot_prod.id]),
        ])
        self.assertEqual(len(lots), 3)

    def test_load_demo_stock_for_traceable_products(self):
        rf = self.env.ref(
            'production_dashboard.pd_comp_rf_serial', raise_if_not_found=False,
        )
        pcb = self.env.ref(
            'production_dashboard.pd_comp_pcb_lot', raise_if_not_found=False,
        )
        if not rf or not pcb:
            self.skipTest('Demo products not installed (upgrade production_dashboard)')

        self.Demo.load_demo_stock()

        rf.invalidate_recordset(['qty_available'])
        pcb.invalidate_recordset(['qty_available'])
        self.assertAlmostEqual(rf.qty_available, 3.0)
        self.assertAlmostEqual(pcb.qty_available, 17.0)

        rf_lots = self.env['stock.lot'].search([('product_id', '=', rf.id)])
        self.assertEqual(len(rf_lots), 3)
        self.assertEqual(
            set(rf_lots.mapped('name')),
            {'SN-GW-RF-001', 'SN-GW-RF-002', 'SN-GW-RF-003'},
        )

        res = self.env['production.estimation.engine'].estimate_by_quantity(
            self.env.ref('production_dashboard.pd_tmpl_fg_gateway').product_variant_ids[0].id,
            self.env.ref('production_dashboard.pd_bom_gateway').id,
            3,
        )
        self.assertAlmostEqual(res['kpis']['real_cost'], 0.0)
        self.assertEqual(res['kpis']['max_qty_from_stock'], 3)