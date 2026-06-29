# -*- coding: utf-8 -*-
"""Idempotent loader for PD demo stock (lots + serials).

Product/BOM definitions live in ``demo_traceable_products.xml``; stock is
applied here so warehouse resolution and inventory adjustment survive DBs
without Odoo demo data (partners, warehouse0, etc.).
"""
import logging

from odoo import api, models

_logger = logging.getLogger(__name__)

# default_code -> list of (lot_name, qty). lot_name=False for untracked stock.
_DEMO_STOCK = {
    'PD-TRK-RF01': [
        ('SN-GW-RF-001', 1.0),
        ('SN-GW-RF-002', 1.0),
        ('SN-GW-RF-003', 1.0),
    ],
    'PD-TRK-PCB01': [
        ('LOT-PCB-2026-A', 12.0),
        ('LOT-PCB-2026-B', 5.0),
    ],
    'PD-TRK-CBL01': [
        (False, 40.0),
    ],
    'PD-TRK-BAT01': [
        ('LOT-BAT-2026-01', 8.0),
    ],
    'PD-TRK-SNS01': [
        ('SN-SNS-001', 1.0),
        ('SN-SNS-002', 1.0),
        ('SN-SNS-003', 1.0),
        ('SN-SNS-004', 1.0),
    ],
    'PD-TRK-ENC01': [
        ('LOT-ENC-2026-A', 15.0),
    ],
}


class ProductionEstimationDemo(models.AbstractModel):
    _name = 'production.estimation.demo'
    _description = 'Production Dashboard Demo Stock Loader'

    @api.model
    def _stock_location(self):
        warehouse = self.env['stock.warehouse'].search(
            [('company_id', '=', self.env.company.id)], limit=1,
        )
        if not warehouse:
            _logger.warning(
                'production_dashboard demo: no warehouse for company %s',
                self.env.company.display_name,
            )
            return self.env['stock.location']
        return warehouse.lot_stock_id

    @api.model
    def _get_or_create_lot(self, product, lot_name):
        Lot = self.env['stock.lot'].sudo()
        lot = Lot.search([
            ('product_id', '=', product.id),
            ('name', '=', lot_name),
        ], limit=1)
        if not lot:
            lot = Lot.create({
                'name': lot_name,
                'product_id': product.id,
                'company_id': product.company_id.id or self.env.company.id,
            })
        return lot

    @api.model
    def _set_inventory(self, product, location, qty, lot=False):
        """Set on-hand qty for one product (optionally one lot/serial)."""
        Quant = self.env['stock.quant'].sudo().with_context(inventory_mode=True)
        domain = [
            ('product_id', '=', product.id),
            ('location_id', '=', location.id),
        ]
        if lot:
            domain.append(('lot_id', '=', lot.id))
        else:
            domain.append(('lot_id', '=', False))
        quant = Quant.search(domain, limit=1)
        vals = {
            'product_id': product.id,
            'location_id': location.id,
            'inventory_quantity': qty,
        }
        if lot:
            vals['lot_id'] = lot.id
        if quant:
            quant.write({'inventory_quantity': qty})
        else:
            quant = Quant.create(vals)
        quant.action_apply_inventory()
        return quant

    @api.model
    def load_demo_stock(self):
        """Create/update demo lots, serials and on-hand quantities."""
        Product = self.env['product.product'].sudo()
        location = self._stock_location()
        if not location:
            return False

        loaded = 0
        for code, lines in _DEMO_STOCK.items():
            product = Product.search([('default_code', '=', code)], limit=1)
            if not product:
                _logger.info(
                    'production_dashboard demo: skip stock for missing %s', code,
                )
                continue
            for lot_name, qty in lines:
                lot = (
                    self._get_or_create_lot(product, lot_name)
                    if lot_name else False
                )
                self._set_inventory(product, location, qty, lot=lot)
                loaded += 1
        _logger.info(
            'production_dashboard demo: applied %d stock line(s) in %s',
            loaded, location.display_name,
        )
        return True