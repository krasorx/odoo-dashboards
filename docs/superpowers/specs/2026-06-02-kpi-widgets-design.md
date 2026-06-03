# KPI Widgets — Design Spec

**Date:** 2026-06-02
**Status:** Approved (pending spec review)
**Target:** Odoo 19, `addons/krasorx/odoo-dashboards`

## Goal

Provide reusable, customizable KPI card widgets for backend views (list & kanban),
rendered in the control-panel header area. A card shows a `label` + a `value`
(number or string) and is optionally clickable to filter the view. KPI values come
from a server-side model method named in the view's arch, so a view becomes
"KPI-enabled" without writing per-view JavaScript.

Two modules:

1. **`kpi_widgets`** — the generic, reusable engine.
2. **`kpi_stock_picking`** — an example consumer that adds delivery/receipt
   stats-by-status on `stock.picking`.

## Conventions (verified against `mrp_stats_header`)

This codebase already ships a working prototype of this exact pattern in
`mrp_stats_header`. We follow its verified Odoo-19 conventions rather than the
generic web plan:

- **Inline OWL templates** (`static template = xml\`...\``) inside each component
  file — not separate `.xml` files for components.
- **Header injection XPath:** inherit `web.ListView` / `web.KanbanView` and inject
  `position="before"` on `//t[@t-component='props.Renderer']`. (This is the
  resolved answer to the generic plan's "verify the control-panel slot" caveat.)
- **Reactive `useState`** for band state; refresh on mount and on search changes.

Deliberate upgrade over `mrp_stats_header`: data is fetched via
`this.orm.call(resModel, kpiMethod, [domain])` (a **model method**), not a custom
`http.route` + `rpc()`. This respects record rules/ACLs and needs no controller
file in the generic module.

## Module 1 — `kpi_widgets`

### Structure

```
kpi_widgets/
├── __manifest__.py
├── static/src/
│   ├── kpi_card/kpi_card.js          # presentational component
│   ├── kpi_band/kpi_band.js          # container component (t-foreach + loading)
│   ├── kpi_hook.js                   # useKpis(): shared fetch + filter logic
│   └── views/
│       ├── kpi_list_view.js          # js_class "kpi_list" + ArchParser + Controller
│       ├── kpi_list_controller.xml   # t-inherit web.ListView -> inject KpiBand
│       ├── kpi_kanban_view.js        # js_class "kpi_kanban" + ArchParser + Controller
│       └── kpi_kanban_controller.xml # t-inherit web.KanbanView -> inject KpiBand
```

Assets registered in `web.assets_backend`.

### `KpiCard` (presentational)

```js
static props = {
    label: String,
    value: [Number, String],
    format: { type: String, optional: true },  // monetary|integer|float|percentage|raw
    icon:   { type: String, optional: true },
    color:  { type: String, optional: true },
    active: { type: Boolean, optional: true },
    onClick:{ type: Function, optional: true }, // onClick(kpi)
};
```

- Zero data logic. Renders `label` + formatted `value`.
- `value` formatting delegated to `@web/views/fields/formatters` keyed by `format`
  (respects locale/currency). Strings and `format="raw"` pass through unchanged;
  unknown `format` falls back to `raw`.
- When `onClick` provided, the card is a `<button>` calling `onClick(kpi)`.
- `active` toggles a highlighted style; styling reuses the Bootstrap/utility
  classes already used by `MrpStatsCard`.

### `KpiBand` (container)

```js
static props = {
    kpis:        Array,                       // [{id, label, value, format?, color?, icon?, domain?}]
    loading:     Boolean,
    activeKpiId: { type: [String, Boolean] },
    onCardClick: Function,                    // onCardClick(kpi)
};
```

- `t-foreach` over `kpis` rendering `KpiCard`, keyed by `kpi.id`.
- Responsive flex/wrap layout in a header bar (mirrors `MrpStatsBanner`'s
  `o_list_view_header` container).
- `loading` → skeleton/spinner state.
- When `activeKpiId` is set, non-active cards are dimmed (`opacity-50`).
- Renders nothing when `kpis` is empty.

### `useKpis` hook (shared DRY logic)

A single hook used by both controllers so fetch/filter logic is not duplicated.

```js
function useKpis() // called inside controller.setup()
```

Behavior:

1. Reads `kpiMethod` from `this.props` (supplied by the ArchParser/extractProps).
2. Holds `useState({ kpis: [], loading: false, activeKpiId: false })`.
3. Fetches on `onMounted` **and** whenever the `searchModel` emits `"UPDATE"`
   (domain/filter change): `this.orm.call(resModel, kpiMethod, [domain])`.
4. `try/catch`: on error → `console.error` + empty `kpis` (view stays usable).
   If `kpiMethod` is falsy → no fetch, band stays empty/hidden.
5. Exposes `toggleFilter(kpi)`:
   - toggles `activeKpiId` between `kpi.id` and `false`;
   - `this.model.load({ domain: [...baseDomain, ...(activeKpiId ? kpi.domain || [] : [])] })`
   - `baseDomain` is the controller's current search domain.

### View integration (list & kanban)

Identical shape per view type:

```js
// kpi_list_view.js
import { listView } from "@web/views/list/list_view";
import { ListController } from "@web/views/list/list_controller";
import { registry } from "@web/core/registry";
import { KpiBand } from "../kpi_band/kpi_band";
import { useKpis } from "../kpi_hook";

class KpiListController extends ListController {
    static template = "kpi_widgets.KpiListController";
    static components = { ...ListController.components, KpiBand };
    setup() {
        super.setup();
        this.kpi = useKpis();
    }
}

// ArchParser captures the root `kpi_method` attribute into archInfo,
// extractProps surfaces it as the `kpiMethod` controller prop.
registry.category("views").add("kpi_list", {
    ...listView,
    Controller: KpiListController,
    ArchParser: KpiListArchParser,
});
```

Template (same idea for kanban with `web.KanbanView`):

```xml
<t t-name="kpi_widgets.KpiListController" t-inherit="web.ListView" t-inherit-mode="primary">
    <xpath expr="//t[@t-component='props.Renderer']" position="before">
        <KpiBand kpis="kpi.kpis" loading="kpi.loading"
                 activeKpiId="kpi.activeKpiId" onCardClick.bind="kpi.toggleFilter"/>
    </xpath>
</t>
```

### Configuration contract (arch)

```xml
<list js_class="kpi_list" kpi_method="get_view_kpis"> … </list>
<kanban js_class="kpi_kanban" kpi_method="get_view_kpis"> … </kanban>
```

The model implements:

```python
def get_view_kpis(self, domain):
    """Return [{id, label, value, format?, color?, icon?, domain?}, ...]
    aggregated over `domain` (the view's current search domain)."""
```

### v19 risk — arch attribute plumbing

The one Odoo-19-specific point to verify empirically: that a custom root attribute
(`kpi_method`) survives the view's `ArchParser` and reaches `extractProps`. We
extend each view's `ArchParser` to read it into `archInfo`, then read it in a
wrapped `extractProps`.

**Fallback if the attribute is stripped:** a JS-side `registry`
(`kpi_widgets.kpi_methods`) mapping `resModel → methodName`, or a fixed
conventional method name (`get_view_kpis`). Resolved during implementation against
the running container (DB `sentios_t1`).

## Module 2 — `kpi_stock_picking` (example)

### Structure

```
kpi_stock_picking/
├── __manifest__.py            # depends: ['stock', 'kpi_widgets']
├── models/
│   ├── __init__.py
│   └── stock_picking.py       # get_view_kpis
└── views/
    └── stock_picking_views.xml # inherit list + kanban: add js_class + kpi_method
```

### `stock.picking.get_view_kpis(self, domain)`

- `read_group` (or `_read_group`) on the **incoming `domain`** grouped by `state`.
- Returns one card per relevant state — `draft`, `waiting`, `confirmed`,
  `assigned`, `done` — with:
  - `id` = state, `label` = translated state label, `value` = count,
  - `format = "integer"`,
  - `color` = state-appropriate (reuse the palette style from `MrpStatsCard`),
  - `domain = [('state', '=', state)]` for click-to-filter.
- Cancelled pickings excluded by default.

### Views

Inherit stock's picking **list** and **kanban** views by XPath, adding
`js_class` + `kpi_method="get_view_kpis"` on the root node.

### Why one method covers deliveries **and** receipts

Stock's standard menus open pickings pre-filtered by picking type — Deliveries with
`picking_type_code = outgoing`, Receipts with `incoming`. Because `useKpis` always
fetches on the **current view domain**, the same method and the same view
inheritance automatically render delivery-stats on the Deliveries view and
receipt-stats on the Receipts view. No per-type branching needed.

## Data flow (end to end)

1. View arch declares `js_class` + `kpi_method`.
2. ArchParser captures `kpi_method` → controller `kpiMethod` prop.
3. `useKpis` fetches on mount and on every searchModel `"UPDATE"`:
   `orm.call(resModel, kpiMethod, [currentDomain])`.
4. `KpiBand` renders `KpiCard`s; `loading` shows a skeleton.
5. Clicking a card with a `domain` toggles `activeKpiId` and reloads the model with
   `baseDomain + kpi.domain`.

## Error handling

| Condition            | Behavior                                            |
|----------------------|-----------------------------------------------------|
| No `kpi_method`      | Band renders nothing; view unaffected.              |
| `orm.call` fails     | `console.error` + empty `kpis`; view still works.   |
| Unknown `format`     | Falls back to `raw`.                                |
| Empty `read_group`   | Cards show `0`.                                     |

## Testing / verification

No JS test infrastructure exists in this repo, so verification is **manual in the
running container** (DB `sentios_t1`):

1. Install `kpi_widgets` + `kpi_stock_picking`.
2. `docker restart odoo_sentios_ee`, update modules (`-u`).
3. Open **Inventory → Deliveries**: confirm the KPI band renders delivery
   stats-by-status reflecting the current domain.
4. Open **Receipts**: confirm the band shows receipt stats-by-status.
5. Click a card → the list/kanban filters to that state; active card highlighted.
6. Apply a search filter → KPI counts update to match.

## Scope / YAGNI

- **In scope:** list + kanban; server-side method data source; click-to-filter;
  formatters by type; the stock example.
- **Out of scope (later):** calendar view (different controller lifecycle);
  declarative `<kpi field=... agg=.../>` arch nodes; refactoring `mrp_stats_header`
  to consume `kpi_widgets`. `mrp_stats_header` is left untouched.
