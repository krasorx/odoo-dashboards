# -*- coding: utf-8 -*-
import base64
import io
import re
from datetime import datetime

import xlsxwriter

from odoo import api, fields, models


class ProductionEstimationExport(models.AbstractModel):
    _name = 'production.estimation.export'
    _description = 'Production Estimation XLSX Export'

    _ROUTE_LABELS = {'manufacture': 'Fabricar', 'buy': 'Comprar'}
    _TRACKING_LABELS = {'serial': 'Serie', 'lot': 'Lote', 'none': 'Sin traza'}

    @api.model
    def _route_label(self, route):
        return self._ROUTE_LABELS.get(route, route or '')

    @api.model
    def _tracking_label(self, tracking):
        return self._TRACKING_LABELS.get(tracking or 'none', tracking or '')

    @api.model
    def _status_label(self, row):
        if row.get('has_stock'):
            return 'OK'
        return 'Faltan %s' % self._fmt_num(row.get('qty_missing', 0))

    @api.model
    def _fmt_num(self, value):
        return round(float(value or 0.0), 4)

    @api.model
    def _walk_tree(self, nodes):
        for node in nodes or []:
            yield node
            yield from self._walk_tree(node.get('children') or [])

    @api.model
    def _aggregate_flat(self, components):
        """Sum quantities and costs per product, ignoring BOM depth."""
        acc = {}
        for node in self._walk_tree(components):
            pid = node['product_id']
            if pid not in acc:
                acc[pid] = {
                    'product_id': pid,
                    'ref': node.get('ref') or '',
                    'name': node['name'],
                    'qty_needed': 0.0,
                    'total_cost': 0.0,
                    'real_cost': 0.0,
                    'qty_available': node.get('qty_available', 0.0),
                    'lead_time': node.get('lead_time', 0.0),
                    'route': node.get('route', 'buy'),
                    'tracking': node.get('tracking', 'none'),
                    'occurrences': 0,
                }
            row = acc[pid]
            row['qty_needed'] += node.get('qty_needed', 0.0)
            row['total_cost'] += node.get('total_cost', 0.0)
            row['real_cost'] += node.get('real_cost', 0.0)
            row['lead_time'] = max(row['lead_time'], node.get('lead_time', 0.0))
            if node.get('route') == 'manufacture':
                row['route'] = 'manufacture'
            row['occurrences'] += 1

        rows = []
        for row in acc.values():
            qty = row['qty_needed']
            available = row['qty_available']
            missing = max(0.0, qty - available)
            row['qty_missing'] = missing
            row['has_stock'] = available >= qty
            row['unit_cost'] = row['total_cost'] / qty if qty else 0.0
            row['depth'] = 0
            rows.append(row)
        rows.sort(key=lambda r: (r['name'] or '').lower())
        return rows

    @api.model
    def _multilevel_rows(self, components):
        """Depth-first tree matching the expanded multilevel dashboard view."""
        rows = []

        def walk(nodes, depth=0):
            for node in nodes or []:
                rows.append({**node, 'depth': depth})
                walk(node.get('children') or [], depth + 1)

        walk(components)
        return rows

    @api.model
    def _component_columns(self, include_level):
        cols = []
        if include_level:
            cols.append(('Nivel', 'depth', 'num'))
        cols.extend([
            ('Referencia', 'ref', 'text'),
            ('Componente', 'name', 'text'),
            ('Cantidad', 'qty_needed', 'num'),
            ('Coste unitario', 'unit_cost', 'money'),
            ('Coste total', 'total_cost', 'money'),
            ('Coste real', 'real_cost', 'money'),
            ('Stock', 'qty_available', 'num'),
            ('Faltante', 'qty_missing', 'num'),
            ('Lead (días)', 'lead_time', 'num'),
            ('Ruta', 'route', 'route'),
            ('Trazabilidad', 'tracking', 'tracking'),
            ('Estado', 'status', 'status'),
        ])
        return cols

    @api.model
    def _workbook_formats(self, workbook):
        return {
            'title': workbook.add_format({
                'bold': True, 'font_name': 'Arial', 'font_size': 14,
                'font_color': '#19140f',
            }),
            'label': workbook.add_format({
                'bold': True, 'font_name': 'Arial', 'font_size': 10,
                'font_color': '#534d44',
            }),
            'value': workbook.add_format({
                'font_name': 'Arial', 'font_size': 10, 'font_color': '#19140f',
            }),
            'header': workbook.add_format({
                'bold': True, 'font_name': 'Arial', 'font_size': 10,
                'font_color': '#ffffff', 'bg_color': '#2d5e8c',
                'border': 1, 'border_color': '#c9c1af', 'align': 'center',
                'valign': 'vcenter', 'text_wrap': True,
            }),
            'text': workbook.add_format({
                'font_name': 'Arial', 'font_size': 10, 'border': 1,
                'border_color': '#ddd6c7', 'valign': 'vcenter',
            }),
            'text_indent': workbook.add_format({
                'font_name': 'Arial', 'font_size': 10, 'border': 1,
                'border_color': '#ddd6c7', 'valign': 'vcenter', 'indent': 1,
            }),
            'num': workbook.add_format({
                'font_name': 'Arial', 'font_size': 10, 'border': 1,
                'border_color': '#ddd6c7', 'num_format': '#,##0.00',
                'align': 'right', 'valign': 'vcenter',
            }),
            'money': workbook.add_format({
                'font_name': 'Arial', 'font_size': 10, 'border': 1,
                'border_color': '#ddd6c7', 'num_format': '#,##0.00',
                'align': 'right', 'valign': 'vcenter',
            }),
            'child': workbook.add_format({
                'font_name': 'Arial', 'font_size': 10, 'border': 1,
                'border_color': '#ddd6c7', 'bg_color': '#f7f3ea',
                'valign': 'vcenter',
            }),
        }

    @api.model
    def _write_summary_sheet(self, sheet, result, export_type, formats):
        product = result.get('product') or {}
        kpis = result.get('kpis') or {}
        mode = result.get('mode', 'quantity')
        now = fields.Datetime.context_timestamp(
            self, fields.Datetime.now(),
        ).strftime('%Y-%m-%d %H:%M')

        sheet.set_column('A:A', 24)
        sheet.set_column('B:B', 42)

        title = 'Estimación de producción — %s' % (
            'acumulado' if export_type == 'flattened' else 'multinivel',
        )
        sheet.write(0, 0, title, formats['title'])

        rows = [
            ('Producto', product.get('name') or ''),
            ('Referencia', product.get('ref') or ''),
            ('Modo', 'Por cantidad' if mode == 'quantity' else 'Por presupuesto'),
        ]
        if mode == 'quantity':
            rows.append(('Cantidad estimada', result.get('qty', 0)))
        else:
            rows.extend([
                ('Presupuesto', result.get('budget', 0)),
                ('Cantidad máxima', result.get('max_qty', 0)),
                ('Presupuesto restante', result.get('remaining', 0)),
            ])
        rows.extend([
            ('Coste unitario', kpis.get('unit_cost', 0)),
            ('Coste total materiales', kpis.get('total_cost', 0)),
            ('Coste real (a comprar)', kpis.get('real_cost', 0)),
            ('Lead time total (días)', kpis.get('total_lead_time', 0)),
            ('% componentes en stock', kpis.get('pct_in_stock', 0)),
            ('Nodos en árbol BoM', kpis.get('tree_nodes_count', 0)),
            ('Análisis', 'Multinivel (completo)'),
            ('Exportado', now),
        ])

        row_idx = 2
        for label, value in rows:
            sheet.write(row_idx, 0, label, formats['label'])
            if isinstance(value, (int, float)) and label not in ('Cantidad máxima',):
                sheet.write(row_idx, 1, float(value), formats['num'])
            else:
                sheet.write(row_idx, 1, value, formats['value'])
            row_idx += 1

    @api.model
    def _cell_value(self, row, col_key, col_type):
        if col_type == 'route':
            return self._route_label(row.get('route'))
        if col_type == 'tracking':
            return self._tracking_label(row.get('tracking'))
        if col_type == 'status':
            return self._status_label(row)
        if col_key == 'name' and row.get('depth', 0) > 0:
            return ('  ' * row['depth']) + (row.get('name') or '')
        return row.get(col_key, '')

    @api.model
    def _write_components_sheet(self, sheet, rows, include_level, formats):
        columns = self._component_columns(include_level)
        for col, (title, _, _) in enumerate(columns):
            sheet.write(0, col, title, formats['header'])

        widths = [8, 14, 34, 12, 14, 14, 14, 12, 12, 12, 12, 14, 16]
        if not include_level:
            widths = widths[1:]
        for col, width in enumerate(widths[:len(columns)]):
            sheet.set_column(col, col, width)

        sheet.freeze_panes(1, 0)
        for r_idx, row in enumerate(rows, start=1):
            depth = row.get('depth', 0)
            for c_idx, (_, key, col_type) in enumerate(columns):
                value = self._cell_value(row, key, col_type)
                if col_type in ('num', 'money'):
                    fmt = formats['num'] if col_type == 'num' else formats['money']
                    if depth > 0 and include_level:
                        fmt = formats.get('child_num') or fmt
                    sheet.write(r_idx, c_idx, float(value or 0), fmt)
                else:
                    fmt = formats['text']
                    if key == 'name' and depth > 0:
                        fmt = formats['text_indent']
                    elif depth > 0 and include_level:
                        fmt = formats['child']
                    sheet.write(r_idx, c_idx, value, fmt)

    @api.model
    def _build_xlsx(self, result, export_type):
        include_level = export_type == 'multilevel'
        components = result.get('components') or []
        if export_type == 'flattened':
            rows = self._aggregate_flat(components)
            sheet_name = 'Componentes acumulados'
        else:
            rows = self._multilevel_rows(components)
            sheet_name = 'Componentes multinivel'

        buffer = io.BytesIO()
        workbook = xlsxwriter.Workbook(buffer, {'in_memory': True})
        formats = self._workbook_formats(workbook)
        formats['child_num'] = workbook.add_format({
            'font_name': 'Arial', 'font_size': 10, 'border': 1,
            'border_color': '#ddd6c7', 'bg_color': '#f7f3ea',
            'num_format': '#,##0.00', 'align': 'right', 'valign': 'vcenter',
        })

        summary = workbook.add_worksheet('Resumen')
        components_sheet = workbook.add_worksheet(sheet_name[:31])
        self._write_summary_sheet(summary, result, export_type, formats)
        self._write_components_sheet(components_sheet, rows, include_level, formats)
        workbook.close()
        buffer.seek(0)
        return buffer.read()

    @api.model
    def _filename(self, result, export_type):
        product = result.get('product') or {}
        ref = product.get('ref') or product.get('name') or 'producto'
        safe = re.sub(r'[^\w\-]+', '_', ref, flags=re.UNICODE).strip('_') or 'producto'
        stamp = datetime.utcnow().strftime('%Y%m%d_%H%M')
        suffix = 'acumulado' if export_type == 'flattened' else 'multinivel'
        return 'estimacion_%s_%s_%s.xlsx' % (safe[:40], suffix, stamp)

    @api.model
    def export(self, export_type, mode, product_id, bom_id=False,
               qty=0, budget=0, filters=None):
        if export_type not in ('flattened', 'multilevel'):
            raise ValueError('export_type must be flattened or multilevel')

        payload = self.env['production.estimation.cache'].run_estimate(
            mode, product_id, bom_id, float(qty or 0), float(budget or 0),
            filters or {},
        )
        result = payload['result']
        content = self._build_xlsx(result, export_type)
        return {
            'filename': self._filename(result, export_type),
            'file': base64.b64encode(content).decode('ascii'),
            'mimetype': (
                'application/vnd.openxmlformats-officedocument'
                '.spreadsheetml.sheet'
            ),
        }