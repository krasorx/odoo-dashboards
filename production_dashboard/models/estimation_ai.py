# -*- coding: utf-8 -*-
"""AI-assisted action planning on top of a production estimation.

The estimation engine already classifies every component as ``buy`` or
``manufacture`` and computes its ``qty_missing``. This model turns that into
an executable plan:

  * purchasables that fall short  -> draft purchase.order(s), grouped by vendor
  * manufacturables that fall short + the finished good -> draft mrp.production

The natural-language summary is produced by a ``custom.agent`` connector when
the ``custom_agent`` module is installed and a connector is configured;
otherwise a deterministic Spanish fallback is used. Plan computation and record
creation are fully deterministic and do NOT depend on the LLM — the agent only
writes the prose, so the feature works even with a placeholder API key.
"""
import logging

from odoo import api, models, _

_logger = logging.getLogger(__name__)


class ProductionEstimationAI(models.AbstractModel):
    _name = 'production.estimation.ai'
    _description = 'Production Estimation AI Assistant'

    # ── Capability detection ────────────────────────────────────────────────
    @api.model
    def is_available(self):
        """True when custom_agent is installed (its model is registered)."""
        return 'custom.agent.connector' in self.env

    @api.model
    def _get_connector(self):
        """Pick a connector for the prose summary.

        Prefers a top-level (non-subagent) connector named like 'MRP', else
        any active top-level connector in the current company. Returns an
        empty recordset when none / module absent."""
        if not self.is_available():
            return self.env['ir.model']  # falsy placeholder
        Conn = self.env['custom.agent.connector'].sudo()
        domain = [('active', '=', True)]
        if 'parent_id' in Conn._fields:
            domain.append(('parent_id', '=', False))
        connectors = Conn.search(domain)
        if not connectors:
            return Conn
        mrp_like = connectors.filtered(lambda c: 'mrp' in (c.name or '').lower())
        return (mrp_like or connectors)[:1]

    @api.model
    def status(self):
        conn = self._get_connector()
        return {
            'available': self.is_available(),
            'connector_id': conn.id if conn else False,
            'connector_name': conn.name if conn else False,
        }

    # ── Plan building ───────────────────────────────────────────────────────
    @api.model
    def _estimate(self, mode, product_id, bom_id, qty, budget, filters):
        out = self.env['production.estimation.cache'].sudo().run_estimate(
            mode, int(product_id), int(bom_id) if bom_id else False,
            float(qty or 0), float(budget or 0), filters or {})
        return out.get('result') or {}

    @api.model
    def _build_plan(self, result):
        """Derive a {purchases, manufactures} plan from an estimation result."""
        Product = self.env['product.product'].sudo()
        prod = result.get('product') or {}
        prod_qty = float(result.get('qty') or 0.0)

        purchases, manufactures = [], []
        # The finished good itself is the production we want to fulfil.
        if prod.get('id') and prod_qty > 0:
            manufactures.append({
                'product_id': prod['id'],
                'name': prod.get('name') or '',
                'qty': round(prod_qty, 2),
                'is_finished': True,
            })

        for c in result.get('components') or []:
            missing = float(c.get('qty_missing') or 0.0)
            if missing <= 0:
                continue
            if c.get('route') == 'buy':
                comp = Product.browse(c['product_id'])
                seller = comp.seller_ids[:1]
                purchases.append({
                    'product_id': c['product_id'],
                    'name': c.get('name') or comp.display_name,
                    'qty': round(missing, 2),
                    'unit_cost': float(c.get('unit_cost') or 0.0),
                    'subtotal': round(missing * float(c.get('unit_cost') or 0.0), 2),
                    'vendor_id': seller.partner_id.id if seller else False,
                    'vendor_name': seller.partner_id.display_name if seller else False,
                    'has_vendor': bool(seller),
                })
            else:  # manufacture
                manufactures.append({
                    'product_id': c['product_id'],
                    'name': c.get('name') or '',
                    'qty': round(missing, 2),
                    'is_finished': False,
                })

        return {
            'purchases': purchases,
            'manufactures': manufactures,
            'purchase_count': len(purchases),
            'manufacture_count': len(manufactures),
            'purchase_total': round(sum(p['subtotal'] for p in purchases), 2),
            'no_vendor': [p['name'] for p in purchases if not p['has_vendor']],
        }

    # ── Summary (LLM, best-effort) ──────────────────────────────────────────
    @api.model
    def _fallback_summary(self, result, plan):
        prod = (result.get('product') or {}).get('name') or _('el producto')
        qty = result.get('qty') or 0
        lines = [_('Plan para fabricar %(q)s × %(p)s:') % {'q': qty, 'p': prod}]
        if plan['purchases']:
            lines.append('')
            lines.append(_('Comprar (%d):') % plan['purchase_count'])
            for p in plan['purchases']:
                v = p['vendor_name'] or _('sin proveedor')
                lines.append('  • %s × %s — %s' % (p['name'], p['qty'], v))
        if plan['manufactures']:
            lines.append('')
            lines.append(_('Fabricar (%d):') % plan['manufacture_count'])
            for m in plan['manufactures']:
                tag = _(' (producto final)') if m['is_finished'] else ''
                lines.append('  • %s × %s%s' % (m['name'], m['qty'], tag))
        if not plan['purchases'] and not plan['manufactures']:
            lines.append(_('Hay stock suficiente: no se requieren compras ni fabricaciones.'))
        if plan['no_vendor']:
            lines.append('')
            lines.append(_('⚠ Sin proveedor configurado: %s') % ', '.join(plan['no_vendor']))
        return '\n'.join(lines)

    @api.model
    def _ai_summary(self, result, plan):
        """Ask the agent to write the action summary; fall back on any error."""
        conn = self._get_connector()
        if not conn:
            return self._fallback_summary(result, plan), False
        try:
            import json
            payload = {
                'producto': (result.get('product') or {}).get('name'),
                'cantidad_a_fabricar': result.get('qty'),
                'kpis': result.get('kpis'),
                'plan': {
                    'comprar': [{'producto': p['name'], 'cantidad': p['qty'],
                                 'proveedor': p['vendor_name']} for p in plan['purchases']],
                    'fabricar': [{'producto': m['name'], 'cantidad': m['qty'],
                                  'producto_final': m['is_finished']}
                                 for m in plan['manufactures']],
                },
            }
            prompt = (
                'Sos un asistente de planificación de producción. A partir de esta '
                'estimación y del plan ya calculado (NO lo recalcules), redactá un '
                'resumen claro y accionable en español rioplatense para un encargado '
                'de planta: qué falta comprar y a quién, qué hay que fabricar, y '
                'cualquier alerta (faltantes sin proveedor, costos, lead time). '
                'Sé conciso, usá viñetas. Datos:\n' + json.dumps(payload, ensure_ascii=False)
            )
            text = conn.raw_chat([{'role': 'user', 'content': prompt}])
            text = (text or '').strip()
            if not text:
                return self._fallback_summary(result, plan), False
            return text, True
        except Exception as exc:
            _logger.info('production_dashboard: AI summary fell back (%s)', exc)
            return self._fallback_summary(result, plan), False

    # ── Public: analyze ─────────────────────────────────────────────────────
    @api.model
    def analyze(self, mode, product_id, bom_id, qty, budget, filters=None):
        result = self._estimate(mode, product_id, bom_id, qty, budget, filters or {})
        if not result:
            return {'available': self.is_available(), 'error': _('Sin estimación.')}
        plan = self._build_plan(result)
        summary, ai_used = self._ai_summary(result, plan)
        status = self.status()
        return {
            'available': True,
            'ai_used': ai_used,
            'connector_name': status['connector_name'],
            'summary': summary,
            'plan': plan,
        }

    # ── Public: execute ─────────────────────────────────────────────────────
    @api.model
    def execute(self, kind, mode, product_id, bom_id, qty, budget, filters=None):
        """Create the records for ``kind`` ('purchase' | 'manufacture').

        The plan is re-derived server-side from the estimation params (never
        trusting client-sent ids/qtys), then the records are created in draft.
        """
        result = self._estimate(mode, product_id, bom_id, qty, budget, filters or {})
        plan = self._build_plan(result)
        if kind == 'purchase':
            return self._create_purchase_orders(plan)
        if kind == 'manufacture':
            return self._create_manufacturing_orders(plan)
        return {'created': [], 'skipped': [], 'message': _('Acción desconocida.')}

    @api.model
    def _base_url(self):
        return (self.env['ir.config_parameter'].sudo()
                .get_param('web.base.url') or '').rstrip('/')

    def _record_url(self, record, action_xmlid):
        base = self._base_url()
        if not base or not record:
            return ''
        return f'{base}/odoo/action-{action_xmlid}/{record.id}'

    @api.model
    def _create_purchase_orders(self, plan):
        company = self.env.company
        PO = self.env['purchase.order'].sudo().with_company(company)
        # Group purchasable shortfalls by vendor; one draft PO per vendor.
        by_vendor = {}
        skipped = []
        for p in plan['purchases']:
            if not p['has_vendor']:
                skipped.append(p['name'])
                continue
            by_vendor.setdefault(p['vendor_id'], []).append(p)
        created = []
        for vendor_id, items in by_vendor.items():
            order_lines = [(0, 0, {'product_id': it['product_id'],
                                   'product_qty': it['qty']}) for it in items]
            po = PO.create({
                'partner_id': vendor_id,
                'company_id': company.id,
                'order_line': order_lines,
            })
            created.append({
                'id': po.id, 'name': po.name,
                'label': po.partner_id.display_name,
                'count': len(items),
                'url': self._record_url(po, 'purchase.purchase_form_action'),
            })
        msg = _('%d orden(es) de compra borrador creada(s).') % len(created)
        if skipped:
            msg += ' ' + _('Sin proveedor (omitidos): %s.') % ', '.join(skipped)
        return {'created': created, 'skipped': skipped, 'message': msg}

    @api.model
    def _create_manufacturing_orders(self, plan):
        company = self.env.company
        MO = self.env['mrp.production'].sudo().with_company(company)
        Engine = self.env['production.estimation.engine'].sudo()
        created, skipped = [], []
        for m in plan['manufactures']:
            product = self.env['product.product'].sudo().browse(m['product_id'])
            bom = Engine._bom_find(product)
            if not bom:
                skipped.append(m['name'])
                continue
            mo = MO.create({
                'product_id': product.id,
                'product_qty': m['qty'],
                'product_uom_id': product.uom_id.id,
                'bom_id': bom.id,
                'company_id': company.id,
            })
            created.append({
                'id': mo.id, 'name': mo.name,
                'label': product.display_name,
                'count': 1,
                'url': self._record_url(mo, 'mrp.mrp_production_action'),
            })
        msg = _('%d orden(es) de fabricación borrador creada(s).') % len(created)
        if skipped:
            msg += ' ' + _('Sin BoM (omitidos): %s.') % ', '.join(skipped)
        return {'created': created, 'skipped': skipped, 'message': msg}
