# KPI Widgets — No-Code Configurable Engine — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make KPI cards fully UI-configurable — an admin defines `kpi.widget` records and the cards appear on that model's list/kanban views with zero code or view edits.

**Architecture:** A `kpi.widget` config model; a generic `get_view_kpis` on `base` that computes cards from config (sudo read, user-rule-respecting aggregates); a `session_info` list of KPI-enabled models; a config-gated global `patch()` of `ListController`/`KanbanController` + `extension` inherits of `web.ListView`/`web.KanbanView` to render the band only for enabled models. The stock example becomes seed data; the old js_class/factory/method path is removed.

**Tech Stack:** Odoo 19, OWL, `@web/core/utils/patch`, `@web/session`, `_read_group`, Docker (`odoo_sentios_ee`, DB `sentios_t1`).

---

## Verified facts (do not re-investigate)

- `patch(objToPatch, extension)` ← `@web/core/utils/patch`.
- `session` ← `@web/session` (`odoo.__session_info__`); read `session.kpi_models`.
- Controllers: `@web/views/list/list_controller` (`ListController`), `@web/views/kanban/kanban_controller` (`KanbanController`). Both use templates `web.ListView` / `web.KanbanView`, each containing `<t t-component="props.Renderer" t-if="model.isReady">`.
- `stock.picking` `state` field xmlid: `stock.field_stock_picking__state`. Model xmlid: `stock.model_stock_picking`.
- `_read_group(domain, ['state'], ['__count'])` → list of tuples like `('assigned', 4)`; for a **selection** groupby the value is the raw key, for **many2one** it is a record, else the raw value. Aggregate spec form: `'field:sum'`, or `'__count'`.
- `@api.model` is REQUIRED on `get_view_kpis` (client calls via `orm.call`; without it `call_kw` treats the first arg as ids). This is a confirmed regression from the prior plan.
- Commands (DB params come from env, pass explicitly):
  - Update: `docker exec odoo_sentios_ee odoo -c /etc/odoo/odoo.conf --db_host=postgres --db_user=odoo --db_password=odoo123 -d sentios_t1 -u <mods> --stop-after-init --no-http`
  - Restart (serves new assets + reloads Python): `docker restart odoo_sentios_ee` then wait ~12s.
  - Shell: `docker exec -i odoo_sentios_ee odoo shell -c /etc/odoo/odoo.conf --db_host=postgres --db_user=odoo --db_password=odoo123 -d sentios_t1 --no-http`
- Git: run from `addons/krasorx/odoo-dashboards` (nested repo).
- No JS test harness — JS validated with `node --check`; behavior verified via shell/`call_kw`/browser.

---

## File Structure

```
kpi_widgets/
├── __init__.py                       # import models
├── __manifest__.py                   # +models/data/security; swap assets
├── models/
│   ├── __init__.py                   # kpi_widget, base_kpi, ir_http
│   ├── kpi_widget.py
│   ├── base_kpi.py
│   └── ir_http.py
├── security/ir.model.access.csv
├── views/
│   ├── kpi_widget_views.xml
│   └── kpi_widget_menus.xml
└── static/src/
    ├── kpi_card/kpi_card.js          # unchanged
    ├── kpi_band/kpi_band.js          # unchanged
    ├── kpi_hook.js                   # generalized
    ├── kpi_patch.js                  # NEW
    └── kpi_patch.xml                 # NEW
# REMOVED: static/src/views/kpi_views.js, static/src/views/kpi_controllers.xml

kpi_stock_picking/
├── __init__.py                       # emptied (no python)
├── __manifest__.py                   # data-only
└── data/kpi_widget_data.xml
# REMOVED: models/, static/, views/stock_picking_views.xml
```

---

## Task 1: `kpi.widget` config model

**Files:**
- Create: `kpi_widgets/models/__init__.py`
- Create: `kpi_widgets/models/kpi_widget.py`
- Edit: `kpi_widgets/__init__.py`

- [ ] **Step 1: Edit `kpi_widgets/__init__.py`**

```python
# -*- coding: utf-8 -*-
from . import models
```

- [ ] **Step 2: Create `kpi_widgets/models/__init__.py`**

```python
# -*- coding: utf-8 -*-
from . import kpi_widget
from . import base_kpi
from . import ir_http
```

- [ ] **Step 3: Create `kpi_widgets/models/kpi_widget.py`**

```python
# -*- coding: utf-8 -*-
from odoo import api, fields, models
from odoo.exceptions import ValidationError

NUMERIC_TYPES = ('integer', 'float', 'monetary')
MINMAX_TYPES = ('integer', 'float', 'monetary', 'date', 'datetime')


class KpiWidget(models.Model):
    _name = 'kpi.widget'
    _description = 'KPI Widget Definition'
    _order = 'sequence, id'

    name = fields.Char(required=True)
    active = fields.Boolean(default=True)
    sequence = fields.Integer(default=10)

    model_id = fields.Many2one('ir.model', string='Model', required=True, ondelete='cascade')
    model_name = fields.Char(related='model_id.model', store=True, index=True)

    card_type = fields.Selection(
        [('aggregate', 'Single value'), ('group_by', 'Group by field')],
        default='aggregate', required=True)

    groupby_field_id = fields.Many2one(
        'ir.model.fields', string='Group by field', ondelete='cascade',
        domain="[('model_id', '=', model_id)]")
    measure_field_id = fields.Many2one(
        'ir.model.fields', string='Measure field', ondelete='cascade',
        domain="[('model_id', '=', model_id)]",
        help="Field to aggregate. Leave empty to count records.")
    aggregate = fields.Selection(
        [('count', 'Count'), ('sum', 'Sum'), ('avg', 'Average'),
         ('max', 'Max'), ('min', 'Min')],
        default='count', required=True)

    domain = fields.Char(default='[]', help="Extra filter applied to this card.")
    label = fields.Char(translate=True, help="Card title (single value). Fallback to name.")
    value_format = fields.Selection(
        [('integer', 'Integer'), ('float', 'Float'), ('monetary', 'Monetary'),
         ('percentage', 'Percentage'), ('raw', 'Raw')],
        string='Format', help="Leave empty for automatic.")
    color = fields.Char(help="Hex color, e.g. #22c55e")
    icon = fields.Char(help="FontAwesome class, e.g. fa fa-truck")

    clickable = fields.Boolean(default=True)
    show_in_list = fields.Boolean(default=True)
    show_in_kanban = fields.Boolean(default=True)

    @api.onchange('model_id')
    def _onchange_model_id(self):
        self.groupby_field_id = False
        self.measure_field_id = False

    @api.constrains('card_type', 'groupby_field_id', 'aggregate', 'measure_field_id')
    def _check_config(self):
        for rec in self:
            if rec.card_type == 'group_by' and not rec.groupby_field_id:
                raise ValidationError("Group-by cards require a 'Group by field'.")
            if rec.aggregate in ('sum', 'avg') and (
                    not rec.measure_field_id or rec.measure_field_id.ttype not in NUMERIC_TYPES):
                raise ValidationError("Sum/Average require a numeric Measure field.")
            if rec.aggregate in ('max', 'min') and (
                    not rec.measure_field_id or rec.measure_field_id.ttype not in MINMAX_TYPES):
                raise ValidationError("Max/Min require a numeric or date Measure field.")
```

- [ ] **Step 4: Verify Python syntax**

Run: `python3 -c "import ast; ast.parse(open('kpi_widgets/models/kpi_widget.py').read()); print('OK')"`
Expected: `OK`

- [ ] **Step 5: Commit**

```bash
git add kpi_widgets/__init__.py kpi_widgets/models/__init__.py kpi_widgets/models/kpi_widget.py
git commit -m "feat(kpi_widgets): add kpi.widget config model"
```

---

## Task 2: Generic `get_view_kpis` on `base`

**Files:**
- Create: `kpi_widgets/models/base_kpi.py`

- [ ] **Step 1: Create `kpi_widgets/models/base_kpi.py`**

```python
# -*- coding: utf-8 -*-
import logging
from odoo import api, models
from odoo.tools.safe_eval import safe_eval

_logger = logging.getLogger(__name__)

NUMERIC_TYPES = ('integer', 'float', 'monetary')


class Base(models.AbstractModel):
    _inherit = 'base'

    @api.model
    def get_view_kpis(self, domain, view_type=None):
        """Compute KPI cards for this model from active kpi.widget config.

        Must be @api.model: called from the client via orm.call, where call_kw
        passes the first positional arg straight through only for model methods.
        Config is read with sudo; aggregates run as the current user (respecting
        record rules). Returns a list of card dicts.
        """
        widgets = self.env['kpi.widget'].sudo().search([
            ('model_name', '=', self._name), ('active', '=', True),
        ])
        if view_type == 'list':
            widgets = widgets.filtered('show_in_list')
        elif view_type == 'kanban':
            widgets = widgets.filtered('show_in_kanban')

        base_domain = domain or []
        cards = []
        for w in widgets:
            try:
                cards.extend(self._kpi_compute_widget(w, base_domain))
            except Exception as e:  # noqa: BLE001 - one bad card must not break the band
                _logger.warning("kpi.widget %s failed for %s: %s", w.id, self._name, e)
        return cards

    @api.model
    def _kpi_compute_widget(self, widget, base_domain):
        extra = safe_eval(widget.domain or '[]')
        full = list(base_domain) + list(extra)
        measure_field = widget.measure_field_id.name or False
        agg = widget.aggregate
        measure_spec = '__count' if (agg == 'count' or not measure_field) else f'{measure_field}:{agg}'
        fmt = widget.value_format or self._kpi_default_format(widget)
        color, icon = widget.color or None, widget.icon or None

        if widget.card_type == 'aggregate':
            rows = self.env[self._name]._read_group(full, [], [measure_spec])
            value = rows[0][0] if rows else 0
            card = {
                'id': f'w{widget.id}',
                'label': widget.label or widget.name,
                'value': value or 0,
                'format': fmt,
            }
            if color:
                card['color'] = color
            if icon:
                card['icon'] = icon
            if widget.clickable:
                card['domain'] = extra
            return [card]

        # group_by
        gb = widget.groupby_field_id.name
        rows = self.env[self._name]._read_group(full, [gb], [measure_spec])
        field = self.env[self._name]._fields[gb]
        cards = []
        for row in rows:
            group_value, measure = row[0], row[1]
            label, key = self._kpi_group_label_key(field, group_value)
            card = {
                'id': f'w{widget.id}_{key}',
                'label': label,
                'value': measure or 0,
                'format': fmt,
            }
            if color:
                card['color'] = color
            if icon:
                card['icon'] = icon
            if widget.clickable:
                card['domain'] = list(extra) + [(gb, '=', key)]
            cards.append(card)
        return cards

    @api.model
    def _kpi_group_label_key(self, field, value):
        """Return (display label, domain key) for a read_group group value."""
        if field.type == 'many2one':
            return (value.display_name if value else 'None'), (value.id if value else False)
        if field.type == 'selection':
            selection = dict(field._description_selection(self.env))
            return selection.get(value, value if value not in (None, False) else 'None'), value
        return (str(value) if value not in (None, False) else 'None'), value

    @api.model
    def _kpi_default_format(self, widget):
        if widget.aggregate == 'count' or not widget.measure_field_id:
            return 'integer'
        if widget.measure_field_id.ttype == 'monetary':
            return 'monetary'
        return 'float'
```

- [ ] **Step 2: Verify Python syntax**

Run: `python3 -c "import ast; ast.parse(open('kpi_widgets/models/base_kpi.py').read()); print('OK')"`
Expected: `OK`

- [ ] **Step 3: Commit**

```bash
git add kpi_widgets/models/base_kpi.py
git commit -m "feat(kpi_widgets): add generic config-driven get_view_kpis on base"
```

---

## Task 3: `session_info` enabled-models list

**Files:**
- Create: `kpi_widgets/models/ir_http.py`

- [ ] **Step 1: Create `kpi_widgets/models/ir_http.py`**

```python
# -*- coding: utf-8 -*-
from odoo import models


class IrHttp(models.AbstractModel):
    _inherit = 'ir.http'

    def session_info(self):
        result = super().session_info()
        models_with_kpis = self.env['kpi.widget'].sudo().search([
            ('active', '=', True),
        ]).mapped('model_name')
        result['kpi_models'] = sorted(set(m for m in models_with_kpis if m))
        return result
```

- [ ] **Step 2: Verify Python syntax**

Run: `python3 -c "import ast; ast.parse(open('kpi_widgets/models/ir_http.py').read()); print('OK')"`
Expected: `OK`

- [ ] **Step 3: Commit**

```bash
git add kpi_widgets/models/ir_http.py
git commit -m "feat(kpi_widgets): expose kpi_models in session_info"
```

---

## Task 4: Security + config views + menu

**Files:**
- Create: `kpi_widgets/security/ir.model.access.csv`
- Create: `kpi_widgets/views/kpi_widget_views.xml`
- Create: `kpi_widgets/views/kpi_widget_menus.xml`

- [ ] **Step 1: Create `kpi_widgets/security/ir.model.access.csv`**

```csv
id,name,model_id:id,group_id:id,perm_read,perm_write,perm_create,perm_unlink
access_kpi_widget_system,kpi.widget.system,model_kpi_widget,base.group_system,1,1,1,1
access_kpi_widget_user,kpi.widget.user,model_kpi_widget,base.group_user,1,0,0,0
```

> Read for all internal users is harmless (config holds no secrets) and avoids edge
> cases; writes restricted to Settings admins. Server computation uses sudo anyway.

- [ ] **Step 2: Create `kpi_widgets/views/kpi_widget_views.xml`**

```xml
<?xml version="1.0" encoding="UTF-8"?>
<odoo>
    <record id="kpi_widget_view_form" model="ir.ui.view">
        <field name="name">kpi.widget.form</field>
        <field name="model">kpi.widget</field>
        <field name="arch" type="xml">
            <form>
                <sheet>
                    <group>
                        <group>
                            <field name="name"/>
                            <field name="model_id" options="{'no_create': True}"/>
                            <field name="model_name" invisible="1"/>
                            <field name="card_type"/>
                            <field name="active"/>
                            <field name="sequence"/>
                        </group>
                        <group>
                            <field name="groupby_field_id"
                                   invisible="card_type != 'group_by'"
                                   required="card_type == 'group_by'"
                                   options="{'no_create': True}"/>
                            <field name="aggregate"/>
                            <field name="measure_field_id"
                                   invisible="aggregate == 'count'"
                                   options="{'no_create': True}"/>
                            <field name="domain"/>
                        </group>
                    </group>
                    <group string="Presentation">
                        <group>
                            <field name="label"/>
                            <field name="value_format"/>
                        </group>
                        <group>
                            <field name="color"/>
                            <field name="icon"/>
                            <field name="clickable"/>
                            <field name="show_in_list"/>
                            <field name="show_in_kanban"/>
                        </group>
                    </group>
                </sheet>
            </form>
        </field>
    </record>

    <record id="kpi_widget_view_list" model="ir.ui.view">
        <field name="name">kpi.widget.list</field>
        <field name="model">kpi.widget</field>
        <field name="arch" type="xml">
            <list>
                <field name="sequence" widget="handle"/>
                <field name="name"/>
                <field name="model_id"/>
                <field name="card_type"/>
                <field name="aggregate"/>
                <field name="active"/>
            </list>
        </field>
    </record>

    <record id="kpi_widget_view_search" model="ir.ui.view">
        <field name="name">kpi.widget.search</field>
        <field name="model">kpi.widget</field>
        <field name="arch" type="xml">
            <search>
                <field name="name"/>
                <field name="model_id"/>
                <filter name="active" string="Active" domain="[('active','=',True)]"/>
                <group expand="0" string="Group By">
                    <filter name="g_model" string="Model" context="{'group_by':'model_id'}"/>
                </group>
            </search>
        </field>
    </record>

    <record id="kpi_widget_action" model="ir.actions.act_window">
        <field name="name">KPI Widgets</field>
        <field name="res_model">kpi.widget</field>
        <field name="view_mode">list,form</field>
    </record>
</odoo>
```

- [ ] **Step 3: Create `kpi_widgets/views/kpi_widget_menus.xml`**

```xml
<?xml version="1.0" encoding="UTF-8"?>
<odoo>
    <menuitem id="menu_kpi_widget_root"
              name="KPI Widgets"
              parent="base.menu_custom"
              action="kpi_widget_action"
              groups="base.group_system"
              sequence="50"/>
</odoo>
```

> `base.menu_custom` is the Settings → Technical menu (confirmed: "Ajustes/Técnico").
> Fallback if ever missing: `base.menu_administration`.

- [ ] **Step 4: Validate XML**

Run:
```bash
for f in kpi_widgets/views/kpi_widget_views.xml kpi_widgets/views/kpi_widget_menus.xml; do
  python3 -c "import xml.dom.minidom,sys; xml.dom.minidom.parse('$f'); print('$f OK')"
done
```
Expected: both print `OK`.

- [ ] **Step 5: Commit**

```bash
git add kpi_widgets/security/ir.model.access.csv kpi_widgets/views/kpi_widget_views.xml kpi_widgets/views/kpi_widget_menus.xml
git commit -m "feat(kpi_widgets): add kpi.widget security, views and menu"
```

---

## Task 5: Generalize `useKpis` hook

**Files:**
- Edit: `kpi_widgets/static/src/kpi_hook.js` (full rewrite)

- [ ] **Step 1: Replace the file contents**

```js
/** @odoo-module */
import { useState, useComponent, onWillStart } from "@odoo/owl";
import { useService, useBus } from "@web/core/utils/hooks";
import { session } from "@web/session";

/**
 * KPI band behavior for a list/kanban controller. Config-gated: does nothing
 * (no RPC) unless the model is in session.kpi_models. Returns { enabled, state,
 * toggleFilter }. Hooks are always registered (OWL rule); load() early-returns
 * when disabled.
 */
export function useKpis(viewType) {
    const component = useComponent();
    const orm = useService("orm");
    const env = component.env;
    const resModel = component.props.resModel;
    const enabled = Array.isArray(session.kpi_models)
        && session.kpi_models.includes(resModel);

    const state = useState({ kpis: [], loading: false, activeKpiId: false });

    async function load() {
        if (!enabled) {
            return;
        }
        state.loading = true;
        try {
            const domain = env.searchModel.domain || [];
            state.kpis = await orm.call(resModel, "get_view_kpis", [domain, viewType]);
        } catch (e) {
            console.error("[kpi_widgets] Error loading KPIs:", e);
            state.kpis = [];
        } finally {
            state.loading = false;
        }
    }

    onWillStart(load);
    useBus(env.searchModel, "UPDATE", () => load());

    async function toggleFilter(kpi) {
        if (!kpi.domain) {
            return;
        }
        const isActive = state.activeKpiId === kpi.id;
        state.activeKpiId = isActive ? false : kpi.id;
        const base = env.searchModel.domain || [];
        const extra = state.activeKpiId ? kpi.domain : [];
        await component.model.load({ domain: [...base, ...extra] });
    }

    return {
        get enabled() {
            return enabled;
        },
        state,
        toggleFilter,
    };
}
```

- [ ] **Step 2: Verify syntax**

Run: `node --check kpi_widgets/static/src/kpi_hook.js`
Expected: PASS (no output).

- [ ] **Step 3: Commit**

```bash
git add kpi_widgets/static/src/kpi_hook.js
git commit -m "feat(kpi_widgets): config-gate useKpis via session.kpi_models"
```

---

## Task 6: Controller patch + template extension

**Files:**
- Create: `kpi_widgets/static/src/kpi_patch.js`
- Create: `kpi_widgets/static/src/kpi_patch.xml`

- [ ] **Step 1: Create `kpi_widgets/static/src/kpi_patch.js`**

```js
/** @odoo-module */
import { patch } from "@web/core/utils/patch";
import { ListController } from "@web/views/list/list_controller";
import { KanbanController } from "@web/views/kanban/kanban_controller";
import { KpiBand } from "./kpi_band/kpi_band";
import { useKpis } from "./kpi_hook";

// Make KpiBand resolvable inside the inherited web.ListView / web.KanbanView
// templates for controllers that use the base components set.
ListController.components = { ...ListController.components, KpiBand };
KanbanController.components = { ...KanbanController.components, KpiBand };

patch(ListController.prototype, {
    setup() {
        super.setup();
        this.kpi = useKpis("list");
    },
});

patch(KanbanController.prototype, {
    setup() {
        super.setup();
        this.kpi = useKpis("kanban");
    },
});
```

> Known limitation (documented in spec): a custom-`js_class` controller that
> re-declares `static components` without spreading the patched base, or overrides
> `static template` to one not inheriting `web.ListView`, won't show the band.
> Plain controllers (incl. stock's `StockListView`, which only swaps the Renderer)
> are covered.

- [ ] **Step 2: Verify syntax**

Run: `node --check kpi_widgets/static/src/kpi_patch.js`
Expected: PASS (no output).

- [ ] **Step 3: Create `kpi_widgets/static/src/kpi_patch.xml`**

```xml
<?xml version="1.0" encoding="UTF-8"?>
<templates xml:space="preserve">

    <t t-name="kpi_widgets.ListViewKpi" t-inherit="web.ListView" t-inherit-mode="extension">
        <xpath expr="//t[@t-component='props.Renderer']" position="before">
            <KpiBand t-if="kpi.enabled"
                     kpis="kpi.state.kpis"
                     loading="kpi.state.loading"
                     activeKpiId="kpi.state.activeKpiId"
                     onCardClick="kpi.toggleFilter"/>
        </xpath>
    </t>

    <t t-name="kpi_widgets.KanbanViewKpi" t-inherit="web.KanbanView" t-inherit-mode="extension">
        <xpath expr="//t[@t-component='props.Renderer']" position="before">
            <KpiBand t-if="kpi.enabled"
                     kpis="kpi.state.kpis"
                     loading="kpi.state.loading"
                     activeKpiId="kpi.state.activeKpiId"
                     onCardClick="kpi.toggleFilter"/>
        </xpath>
    </t>

</templates>
```

- [ ] **Step 4: Validate XML**

Run: `python3 -c "import xml.dom.minidom; xml.dom.minidom.parse('kpi_widgets/static/src/kpi_patch.xml'); print('OK')"`
Expected: `OK`

- [ ] **Step 5: Commit**

```bash
git add kpi_widgets/static/src/kpi_patch.js kpi_widgets/static/src/kpi_patch.xml
git commit -m "feat(kpi_widgets): config-gated patch of list/kanban controllers"
```

---

## Task 7: Update `kpi_widgets` manifest + remove superseded files

**Files:**
- Edit: `kpi_widgets/__manifest__.py`
- Delete: `kpi_widgets/static/src/views/kpi_views.js`
- Delete: `kpi_widgets/static/src/views/kpi_controllers.xml`

- [ ] **Step 1: Replace `kpi_widgets/__manifest__.py`**

```python
# -*- coding: utf-8 -*-
{
    'name': 'KPI Widgets',
    'version': '19.0.2.0.0',
    'category': 'Productivity',
    'summary': 'No-code configurable KPI cards in the header of list and kanban views',
    'depends': ['web'],
    'data': [
        'security/ir.model.access.csv',
        'views/kpi_widget_views.xml',
        'views/kpi_widget_menus.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'kpi_widgets/static/src/kpi_card/kpi_card.js',
            'kpi_widgets/static/src/kpi_band/kpi_band.js',
            'kpi_widgets/static/src/kpi_hook.js',
            'kpi_widgets/static/src/kpi_patch.js',
            'kpi_widgets/static/src/kpi_patch.xml',
        ],
    },
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}
```

- [ ] **Step 2: Delete the superseded files**

```bash
git rm kpi_widgets/static/src/views/kpi_views.js kpi_widgets/static/src/views/kpi_controllers.xml
```

- [ ] **Step 3: Commit**

```bash
git add kpi_widgets/__manifest__.py
git commit -m "refactor(kpi_widgets): switch manifest to config engine; drop js_class factories"
```

---

## Task 8: Migrate `kpi_stock_picking` to data-only

**Files:**
- Edit: `kpi_stock_picking/__init__.py` (empty it)
- Edit: `kpi_stock_picking/__manifest__.py`
- Create: `kpi_stock_picking/data/kpi_widget_data.xml`
- Delete: `kpi_stock_picking/models/` (whole dir), `kpi_stock_picking/static/` (whole dir), `kpi_stock_picking/views/stock_picking_views.xml`

- [ ] **Step 1: Replace `kpi_stock_picking/__init__.py`**

```python
# -*- coding: utf-8 -*-
```

- [ ] **Step 2: Create `kpi_stock_picking/data/kpi_widget_data.xml`**

```xml
<?xml version="1.0" encoding="UTF-8"?>
<odoo>
    <record id="kpi_picking_by_state" model="kpi.widget">
        <field name="name">Pickings by status</field>
        <field name="model_id" ref="stock.model_stock_picking"/>
        <field name="card_type">group_by</field>
        <field name="groupby_field_id" ref="stock.field_stock_picking__state"/>
        <field name="aggregate">count</field>
        <field name="value_format">integer</field>
        <field name="clickable" eval="True"/>
    </record>
</odoo>
```

- [ ] **Step 3: Replace `kpi_stock_picking/__manifest__.py`**

```python
# -*- coding: utf-8 -*-
{
    'name': 'KPI Widgets - Stock Picking Example',
    'version': '19.0.2.0.0',
    'category': 'Inventory',
    'summary': 'Example: delivery/receipt KPI cards by status, configured (no code)',
    'depends': ['stock', 'kpi_widgets'],
    'data': [
        'data/kpi_widget_data.xml',
    ],
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}
```

- [ ] **Step 4: Delete superseded dirs/files**

```bash
git rm -r kpi_stock_picking/models kpi_stock_picking/static kpi_stock_picking/views
```

- [ ] **Step 5: Validate XML + commit**

Run: `python3 -c "import xml.dom.minidom; xml.dom.minidom.parse('kpi_stock_picking/data/kpi_widget_data.xml'); print('OK')"`
Expected: `OK`

```bash
git add kpi_stock_picking/__init__.py kpi_stock_picking/__manifest__.py kpi_stock_picking/data/kpi_widget_data.xml
git commit -m "refactor(kpi_stock_picking): become data-only config example"
```

---

## Task 9: Install/update + restart

**Files:** none

- [ ] **Step 1: Update both modules**

Run:
```bash
docker exec odoo_sentios_ee odoo -c /etc/odoo/odoo.conf --db_host=postgres --db_user=odoo --db_password=odoo123 -d sentios_t1 -u kpi_widgets,kpi_stock_picking --stop-after-init --no-http 2>&1 | grep -iE "module kpi_widgets loaded|module kpi_stock_picking loaded|Modules loaded|ERROR|CRITICAL|Traceback|ParseError|External ID" | tail -20
```
Expected: both modules load, `Modules loaded.`, no ERROR/Traceback. If `External ID` error on `base.menu_custom` or `stock.field_stock_picking__state`, fix the ref and re-run.

- [ ] **Step 2: Restart to serve assets + reload Python**

Run: `docker restart odoo_sentios_ee` then wait ~12s.
Verify: `docker ps --filter name=odoo_sentios_ee --format '{{.Status}}'` shows recent uptime, and `docker exec odoo_sentios_ee bash -lc 'curl -s -o /dev/null -w "%{http_code}" http://localhost:8069/web/login'` returns `303`.

---

## Task 10: Verification

**Files:** none

- [ ] **Step 1: Generic compute — group_by (shell)**

Run the shell with:
```python
res = env['stock.picking'].get_view_kpis([['picking_type_code','=','outgoing']], 'list')
print("OUT:", [(k['id'], k['label'], k['value']) for k in res])
assert res, "expected cards from seed config"
assert all('domain' in k for k in res), "clickable cards must carry a domain"
print("OK")
```
Expected: one card per state with counts, labels localized, each with a `domain`; `OK`.

- [ ] **Step 2: Generic compute — aggregate/sum (shell, ad-hoc widget)**

Run the shell with:
```python
W = env['kpi.widget']
f = env['ir.model.fields'].search([('model','=','stock.picking'),('name','=','weight')], limit=1)
w = W.create({'name':'Total weight','model_id':env.ref('stock.model_stock_picking').id,
              'card_type':'aggregate','aggregate':'sum','measure_field_id':f.id})
out = env['stock.picking'].get_view_kpis([], 'list')
print("CARDS:", [(k['label'], k['value'], k['format']) for k in out])
assert any(k['label']=='Total weight' for k in out)
w.unlink()
print("OK")
```
Expected: includes a `Total weight` card with `format` `float`; `OK`. (If `weight` is absent on this build, substitute any numeric field printed by `env['ir.model.fields'].search([('model','=','stock.picking'),('ttype','in',('float','monetary','integer'))]).mapped('name')`.)

- [ ] **Step 3: RPC path (call_kw) guards the @api.model regression**

Run the shell with:
```python
from odoo.service.model import call_kw
r = call_kw(env['stock.picking'], 'get_view_kpis', [[], 'list'], {})
print("CALL_KW OK:", len(r), "cards")
```
Expected: prints a card count, no exception.

- [ ] **Step 4: session_info exposes the model**

Run the shell with:
```python
info = env['ir.http'].session_info()
print("kpi_models:", info.get('kpi_models'))
assert 'stock.picking' in info.get('kpi_models', [])
print("OK")
```
Expected: list contains `stock.picking`; `OK`.

- [ ] **Step 5: Browser checks**

1. Open **Inventory → Deliveries**: KPI band shows status cards (non-zero from earlier seeded pickings); clicking a card filters the list and highlights it.
2. Open **Receipts**: band reflects incoming pickings.
3. Switch to **kanban** on either: band renders there too.
4. Open **Contacts** (a model with no `kpi.widget`): **no band**, and no `get_view_kpis` request in the browser Network tab.
5. **Settings → Technical → KPI Widgets**: the list shows the seeded "Pickings by status"; create a new aggregate card on another model, refresh, confirm it appears on that model's list.

- [ ] **Step 6: Final commit (empty if no fixes needed)**

```bash
git commit --allow-empty -m "test(kpi_widgets): verify config-driven engine end-to-end"
```

---

## Self-Review Notes

- **Spec coverage:** config model (T1), generic compute incl. both card kinds + all aggregates + group label/key + auto format (T2), session_info (T3), security/menu/views (T4), generalized hook (T5), config-gated patch + template extension (T6), manifest swap + removal of factories/old templates (T7), stock→data migration + removal of old python/views/assets (T8), install/restart (T9), verification incl. the `@api.model` regression guard and the "no band/no RPC for unconfigured model" check (T10). All spec sections map to tasks.
- **Type/name consistency:** card dict keys (`id,label,value,format,color?,icon?,domain?`) match `KpiCard` props and `KpiBand` foreach (unchanged components). Hook returns `{enabled, state:{kpis,loading,activeKpiId}, toggleFilter}` — matched by `kpi.enabled` / `kpi.state.*` / `kpi.toggleFilter` in `kpi_patch.xml`. `get_view_kpis(domain, view_type)` signature matches the hook's `orm.call(..., [domain, viewType])` and the call_kw test.
- **Field name note:** model field is `value_format` (not `format`, which is reserved-ish/confusing); the computed card key remains `format` as `KpiCard` expects. Mapping done in `_kpi_compute_widget`.
- **Runtime-confirmed refs (executor must verify, fallbacks given):** `base.menu_custom` (T4), `stock.model_stock_picking` + `stock.field_stock_picking__state` (T8) — the latter two were confirmed during planning.
- **Open risk:** patch component-resolution for subclassed controllers that re-declare `static components` (documented limitation in T6 + spec); plain controllers and stock are covered.
