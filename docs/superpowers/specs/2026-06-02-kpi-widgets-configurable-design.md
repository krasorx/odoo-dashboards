# KPI Widgets — No-Code Configurable Engine — Design Spec

**Date:** 2026-06-02
**Status:** Approved (pending spec review)
**Target:** Odoo 19, `addons/krasorx/odoo-dashboards`
**Builds on:** `2026-06-02-kpi-widgets-design.md` (the initial js_class + method engine)

## Goal

Let anyone configure KPI cards on **any list/kanban view, for any field, without
touching code**. An admin defines cards in a UI (`kpi.widget` records); the cards
appear automatically on that model's list and kanban views — no view edits, no
Python per model.

This supersedes the initial engine's two code touch-points (`js_class` on the arch
+ a per-model `get_view_kpis` method) with: a config model, one generic computation
method on `base`, and a config-gated global controller patch.

## Decisions (from brainstorming)

- **Attach method:** config-gated **global patch** of the base
  `ListController`/`KanbanController` + a one-time inherit of `web.ListView` /
  `web.KanbanView` templates. Behavior is gated on per-model config, so unconfigured
  models do nothing (one array check, no RPC). Works on top of *any* existing
  `js_class`.
- **Card kinds:** both **single-value aggregate** and **group-by** cards.
- **Aggregations:** count, sum, avg, min, max.
- **Stock example:** migrated to **seed config data** (no Python, no view edits).
- **Chosen defaults:** menu under Settings → Technical, `base.group_system` only;
  config read with `sudo` (end users need no ACL); enabled-models list shipped via
  `session_info` (new config visible after a page refresh); group-by cards clickable
  by default.

## Architecture overview

```
kpi_widgets/
├── models/
│   ├── kpi_widget.py        # kpi.widget config model + helpers
│   ├── base_kpi.py          # _inherit='base': get_view_kpis(domain, view_type)
│   └── ir_http.py           # session_info -> kpi_models list
├── security/
│   ├── ir.model.access.csv  # kpi.widget access (admins write; sudo handles reads)
│   └── kpi_widgets_security.xml (optional dedicated group — see Security)
├── views/
│   ├── kpi_widget_views.xml # form/list/search + action
│   └── kpi_widget_menus.xml # Settings -> Technical -> KPI Widgets
├── static/src/
│   ├── kpi_card/kpi_card.js      # KEPT (presentational)
│   ├── kpi_band/kpi_band.js      # KEPT (container)
│   ├── kpi_hook.js               # GENERALIZED useKpis()
│   └── kpi_patch.js              # NEW: patch List/Kanban controllers + templates
│   └── kpi_patch.xml             # NEW: inherit web.ListView / web.KanbanView
└── __manifest__.py

kpi_stock_picking/                # becomes pure data
├── data/kpi_widget_data.xml      # one group-by-state kpi.widget for stock.picking
└── __manifest__.py               # depends: stock, kpi_widgets; data only
```

**Removed (superseded):** `kpi_widgets/static/src/views/kpi_views.js`
(`makeKpiListView`/`makeKpiKanbanView` + `kpi_list`/`kpi_kanban` registration),
`kpi_widgets/static/src/views/kpi_controllers.xml`,
`kpi_stock_picking/models/*`, `kpi_stock_picking/static/*`,
`kpi_stock_picking/views/stock_picking_views.xml`.

## Component 1 — `kpi.widget` config model

`models/kpi_widget.py`, `_name = 'kpi.widget'`, `_order = 'sequence, id'`.

| Field | Type | Notes |
|---|---|---|
| `name` | Char, required | Internal label / fallback card label |
| `model_id` | Many2one `ir.model`, required, ondelete cascade | Target model |
| `model_name` | Char, related `model_id.model`, stored, indexed | Fast lookup key |
| `card_type` | Selection `[('aggregate','Single value'),('group_by','Group by field')]`, default `aggregate` | |
| `groupby_field_id` | Many2one `ir.model.fields` | Field to group by (group_by only) |
| `measure_field_id` | Many2one `ir.model.fields` | Field to aggregate; blank ⇒ count |
| `aggregate` | Selection `count/sum/avg/max/min`, default `count` | |
| `domain` | Char, default `'[]'` | Extra filter, safe_eval |
| `label` | Char, translatable | Card title (aggregate); prefix/fallback (group_by) |
| `format` | Selection `integer/float/monetary/percentage/raw`, optional | Blank ⇒ auto (see Compute) |
| `color` | Char | hex (e.g. `#22c55e`) or empty |
| `icon` | Char | FontAwesome class, e.g. `fa fa-truck` |
| `clickable` | Boolean, default True | Click filters the view |
| `show_in_list` | Boolean, default True | |
| `show_in_kanban` | Boolean, default True | |
| `sequence` | Integer, default 10 | |
| `active` | Boolean, default True | |

**Field-domain helpers (onchange/domain):**
- `groupby_field_id` and `measure_field_id` are domain-limited to
  `[('model_id','=', model_id)]`.
- When `aggregate in (sum,avg,min,max)`, `measure_field_id` is required and limited to
  numeric/date types (`ttype in ('integer','float','monetary','date','datetime')`;
  min/max also allow date/datetime, sum/avg only numeric).
- Python `@api.constrains` enforces: group_by ⇒ `groupby_field_id` set; non-count
  aggregate ⇒ numeric `measure_field_id`.

## Component 2 — generic `get_view_kpis` on `base`

`models/base_kpi.py`, `_inherit = 'base'`.

```python
@api.model
def get_view_kpis(self, domain, view_type=None):
    """Compute KPI cards for self._name from active kpi.widget config.
    Read config with sudo; compute with the calling user's rules.
    Returns [{id,label,value,format,color,icon,domain?}, ...]."""
```

Algorithm:
1. `widgets = self.env['kpi.widget'].sudo().search([('model_name','=',self._name),('active','=',True)], order='sequence,id')`.
2. Filter by `view_type` (`show_in_list` / `show_in_kanban`) when provided.
3. For each widget, wrapped in try/except (skip + `_logger.warning` on error):
   - `base = safe_eval(widget.domain or '[]')`; `full = (domain or []) + base`.
   - measure spec: `'__count'` if no `measure_field_id` else
     `f'{measure_field}:{aggregate}'`.
   - **aggregate card:** one `_read_group(full, [], [measure_spec])` row → value;
     emit one card `{id: f'w{widget.id}', label: widget.label or widget.name,
     value, format: resolved_format, color, icon,
     domain: base if widget.clickable else None}`.
   - **group_by card:** `_read_group(full, [groupby_field], [measure_spec])` →
     for each `(group_value, measure)` emit a card
     `{id: f'w{widget.id}_{key}', label: <group label>, value: measure, ...,
     domain: base + [(groupby_field,'=', group_value_id_or_value)]}` when clickable.
     Group label: use the read_group display value (selection label / m2o name /
     raw); fall back to `str(value)`. `False` group → label from widget or "None".
4. **Format resolution** when `widget.format` blank: `integer` for count;
   `monetary` if measure field is `monetary`; `float` otherwise.

Still overridable per-model (a model may define its own `get_view_kpis`).

## Component 3 — `session_info` enabled-models list

`models/ir_http.py`, `_inherit = 'ir.http'`:

```python
def session_info(self):
    result = super().session_info()
    models = self.env['kpi.widget'].sudo().search([('active','=',True)]).mapped('model_name')
    result['kpi_models'] = sorted(set(models))
    return result
```

Client reads `session.kpi_models` (`@web/session`) — no extra RPC. New config
appears after a page refresh (acceptable; admin-time change).

## Component 4 — config-gated controller patch

`static/src/kpi_patch.js`:

- Import `ListController`, `KanbanController`, `KpiBand`, `useKpis`, `patch`,
  `session`.
- Add `KpiBand` to each controller's components:
  `ListController.components = { ...ListController.components, KpiBand };` (same for
  kanban).
- `patch(ListController.prototype, { setup() { super.setup(); this.kpi = useKpis("list"); } })`
  and the kanban equivalent with `"kanban"`.

`useKpis(viewType)` (generalized hook):
- Reads `resModel = component.props.resModel`.
- `enabled = session.kpi_models?.includes(resModel)`.
- Always registers hooks (OWL rule), but `load()` early-returns when `!enabled`.
- Exposes `state` and `toggleFilter` (unchanged behavior), plus `enabled` getter.
- Passes `view_type` to the RPC: `orm.call(resModel, "get_view_kpis", [domain, viewType])`.

`static/src/kpi_patch.xml` — inherit both base templates (primary), gate on
`kpi.enabled`:

```xml
<t t-name="kpi_widgets.ListViewKpi" t-inherit="web.ListView" t-inherit-mode="extension">
    <xpath expr="//t[@t-component='props.Renderer']" position="before">
        <KpiBand t-if="kpi.enabled" kpis="kpi.state.kpis" loading="kpi.state.loading"
                 activeKpiId="kpi.state.activeKpiId" onCardClick="kpi.toggleFilter"/>
    </xpath>
</t>
```
(and `kpi_widgets.KanbanViewKpi` inheriting `web.KanbanView`.) Using
`t-inherit-mode="extension"` so we extend the shared base template in place; every
list/kanban controller using `web.ListView`/`web.KanbanView` gets the band slot,
rendered only when `kpi.enabled`.

> Edge case: a custom `js_class` controller that overrides `static template` to a
> template NOT inheriting `web.ListView` won't get the band. Out of scope; rare.

## Component 5 — `kpi_stock_picking` as data

`data/kpi_widget_data.xml` — one record:

```xml
<record id="kpi_picking_by_state" model="kpi.widget">
    <field name="name">Pickings by status</field>
    <field name="model_id" ref="stock.model_stock_picking"/>
    <field name="card_type">group_by</field>
    <field name="groupby_field_id" ref="stock.field_stock_picking__state"/>
    <field name="aggregate">count</field>
    <field name="clickable" eval="True"/>
</record>
```

Manifest: `depends: ['stock','kpi_widgets']`, `data: ['data/kpi_widget_data.xml']`,
no assets, no models. (`ref` for the state field: confirm xmlid
`stock.field_stock_picking__state` at implementation time.)

## Security

- `ir.model.access.csv`: `kpi.widget` — read/write/create/unlink for
  `base.group_system`; no general user access needed (computation uses `sudo`).
- Menu/action gated to `base.group_system`.
- `domain` is admin-authored and evaluated with `safe_eval` (no arbitrary code).
- Aggregates run as the calling user → respect record rules. Config reads use `sudo`.

## Error handling

| Condition | Behavior |
|---|---|
| Model not in `session.kpi_models` | No RPC, band hidden (one array check) |
| Bad `domain` / missing field in a widget | That card skipped + `_logger.warning`; others render |
| `aggregate` non-count without numeric field | Blocked at config time by `@api.constrains` |
| Unknown `format` | Falls back to `raw` (KpiCard) |
| RPC error | `console.error` + empty kpis (existing hook behavior) |

## Testing / verification

No JS test harness; verification is programmatic + manual:
1. `odoo shell`: create a `kpi.widget` (group_by state on `stock.picking`), call
   `env['stock.picking'].get_view_kpis([], 'list')` → correct cards; also an
   `aggregate`/sum widget on a numeric field → correct single value.
2. Reproduce the client path via `from odoo.service.model import call_kw` →
   `call_kw(env['stock.picking'],'get_view_kpis',[[], 'list'], {})` succeeds
   (guards the `@api.model` regression).
3. `session_info()` includes `stock.picking` in `kpi_models`.
4. Browser: Deliveries/Receipts show the band (from seed data); a model with no
   config (e.g. Contacts) shows no band and issues no `get_view_kpis` RPC (verify in
   network tab / server logs).

## Scope / YAGNI

- **In scope:** config model, generic compute on `base`, session_info, controller
  patch, stock seed data, removal of superseded code.
- **Out of scope (later):** pivot/graph views; per-action (vs per-model) configs;
  live refresh without page reload; drag-reorder UI; computed/expression measures
  beyond stored fields; non-list/kanban views.
