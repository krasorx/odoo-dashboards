# -*- coding: utf-8 -*-
from odoo.tests.common import TransactionCase


class ProdEstCommon(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        Product = cls.env['product.product']
        Bom = cls.env['mrp.bom']

        cls.mfg_route = cls.env.ref('mrp.route_warehouse0_manufacture')

        # Raw material (bought)
        cls.r1 = Product.create({
            'name': 'PD Raw R1', 'type': 'consu', 'is_storable': True,
            'standard_price': 10.0,
        })
        # Bought component
        cls.c1 = Product.create({
            'name': 'PD Comp C1', 'type': 'consu', 'is_storable': True,
            'standard_price': 25.0,
        })
        # Manufactured subassembly
        cls.sa = Product.create({
            'name': 'PD SubAsm SA', 'type': 'consu', 'is_storable': True,
            'standard_price': 0.0,
            'route_ids': [(6, 0, [cls.mfg_route.id])],
        })
        # Finished good (manufactured)
        cls.fg = Product.create({
            'name': 'PD Finished FG', 'type': 'consu', 'is_storable': True,
            'standard_price': 0.0,
            'route_ids': [(6, 0, [cls.mfg_route.id])],
        })

        # BOM SA = 4 x R1 (manufacturing lead time 2 days)
        cls.bom_sa = Bom.create({
            'product_tmpl_id': cls.sa.product_tmpl_id.id,
            'product_qty': 1.0,
            'type': 'normal',
            'produce_delay': 2,
            'bom_line_ids': [(0, 0, {'product_id': cls.r1.id, 'product_qty': 4.0})],
        })
        # BOM FG = 2 x SA + 3 x C1 (manufacturing lead time 3 days)
        cls.bom_fg = Bom.create({
            'product_tmpl_id': cls.fg.product_tmpl_id.id,
            'product_qty': 1.0,
            'type': 'normal',
            'produce_delay': 3,
            'bom_line_ids': [
                (0, 0, {'product_id': cls.sa.id, 'product_qty': 2.0}),
                (0, 0, {'product_id': cls.c1.id, 'product_qty': 3.0}),
            ],
        })
        cls.Cache = cls.env['production.estimation.cache']
