# -*- coding: utf-8 -*-
import base64
import io
import zipfile

from odoo.tests.common import tagged
from .common import ProdEstCommon


@tagged('post_install', '-at_install')
class TestEstimationExport(ProdEstCommon):

    def setUp(self):
        super().setUp()
        self.Export = self.env['production.estimation.export']
        self.Engine = self.env['production.estimation.engine']

    def _result(self, qty=1):
        return self.Engine.estimate_by_quantity(self.fg.id, self.bom_fg.id, qty)

    def _rows_from_xlsx(self, content, sheet_index=1):
        try:
            import openpyxl
        except ImportError:
            self.skipTest('openpyxl not installed')
        wb = openpyxl.load_workbook(io.BytesIO(content), read_only=True, data_only=True)
        sheet = wb.worksheets[sheet_index]
        return [list(row) for row in sheet.iter_rows(values_only=True)]

    def test_flattened_aggregates_tree_products(self):
        result = self._result(1)
        rows = self.Export._aggregate_flat(result['components'])
        by_id = {r['product_id']: r for r in rows}
        self.assertEqual(len(by_id), 3)
        self.assertAlmostEqual(by_id[self.r1.id]['qty_needed'], 8.0)
        self.assertAlmostEqual(by_id[self.sa.id]['qty_needed'], 2.0)
        self.assertAlmostEqual(by_id[self.c1.id]['qty_needed'], 3.0)
        self.assertAlmostEqual(by_id[self.r1.id]['total_cost'], 80.0)

    def test_multilevel_preserves_depth(self):
        result = self._result(1)
        rows = self.Export._multilevel_rows(result['components'])
        depths = {r['product_id']: r['depth'] for r in rows}
        self.assertEqual(depths[self.sa.id], 0)
        self.assertEqual(depths[self.c1.id], 0)
        self.assertEqual(depths[self.r1.id], 1)
        self.assertEqual(len(rows), 3)

    def test_export_flattened_xlsx(self):
        payload = self.Export.export(
            'flattened', 'quantity', self.fg.id, self.bom_fg.id, qty=1,
        )
        raw = base64.b64decode(payload['file'])
        self.assertTrue(raw.startswith(b'PK'))
        self.assertIn('acumulado', payload['filename'])
        with zipfile.ZipFile(io.BytesIO(raw)) as zf:
            self.assertTrue(any(n.startswith('xl/') for n in zf.namelist()))

    def test_export_multilevel_xlsx(self):
        payload = self.Export.export(
            'multilevel', 'quantity', self.fg.id, self.bom_fg.id, qty=1,
        )
        raw = base64.b64decode(payload['file'])
        self.assertTrue(raw.startswith(b'PK'))
        self.assertIn('multinivel', payload['filename'])
        table = self._rows_from_xlsx(raw)
        header = table[0]
        self.assertIn('Nivel', header)
        r1_row = next(r for r in table[1:] if r[2] and 'R1' in str(r[2]))
        self.assertEqual(r1_row[0], 1)