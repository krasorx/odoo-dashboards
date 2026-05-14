# BOM Dashboard Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Crear el addon `bom_dashboard` para Odoo 19 con dos vistas (Estructura BOM y MOs Activas) organizadas por nivel de BOM, con sidebar de navegación compartido, y publicar el repositorio en GitHub como `krasorx/odoo-dashboards`.

**Architecture:** Addon OWL + Tailwind CDN siguiendo el patrón de `mrp_dashboard`. Un controlador Python expone `/bom/dashboard/boms` y `/bom/dashboard/data` que devuelven el árbol de BOM expandido recursivamente (máx 10 niveles) con las MOs activas por producto. El componente raíz `BomDashboard` gestiona estado global; `BomLevelColumn` renderiza columnas agrupadas por padre; las vistas `BomStructureView` y `BomMoView` son tabs que comparten el mismo getter `visibleColumns`.

**Tech Stack:** Odoo 19, OWL 2, Tailwind CSS CDN, Python 3, GitHub CLI (`gh`)

---

## File Map

| Archivo | Responsabilidad |
|---|---|
| `bom_dashboard/__manifest__.py` | Metadatos del addon, assets JS |
| `bom_dashboard/__init__.py` | Importa `controllers` |
| `bom_dashboard/controllers/__init__.py` | Importa `bom_dashboard_controller` |
| `bom_dashboard/controllers/bom_dashboard_controller.py` | Rutas JSON: `/bom/dashboard/boms` y `/bom/dashboard/data` |
| `bom_dashboard/security/ir.model.access.csv` | Sin modelos nuevos — archivo mínimo requerido |
| `bom_dashboard/views/bom_dashboard_menu.xml` | Acción cliente + menuitem Manufacturing |
| `bom_dashboard/static/src/js/bom_dashboard_action.js` | Registra BomDashboard en el registry de acciones |
| `bom_dashboard/static/src/js/components/bom_colors.js` | Constantes de colores por nivel (LEVEL_BADGES, LEVEL_COLOR) |
| `bom_dashboard/static/src/js/components/BomProductCard.js` | Card de producto (manufacturado con borde sólido, comprado con ✓) |
| `bom_dashboard/static/src/js/components/MoBomCard.js` | Card de MO (avatar, referencia, qty/estado) |
| `bom_dashboard/static/src/js/components/BomLevelColumn.js` | Columna de nivel: header badge, grupos por padre, card rendering |
| `bom_dashboard/static/src/js/components/BomSidebar.js` | Sidebar: lista de BOMs + buscador local + filtro estado |
| `bom_dashboard/static/src/js/components/BomStructureView.js` | Tab "Estructura BOM": columnas de productos |
| `bom_dashboard/static/src/js/components/BomMoView.js` | Tab "MOs Activas": columnas de MOs + refresh |
| `bom_dashboard/static/src/js/components/BomDashboard.js` | Root: sidebar + tabs + estado global + `visibleColumns` getter |

---

## Task 1: Git repo + GitHub

**Files:**
- Create: `.gitignore`
- GitHub: repo `krasorx/odoo-dashboards`

- [ ] **Step 1: Crear .gitignore**

```
# Python
__pycache__/
*.pyc
*.pyo
.eggs/

# Odoo
*.log
.odoo_history

# Node / Tailwind
node_modules/

# Editor
.vscode/
.idea/
*.swp

# Sistema
.DS_Store
Thumbs.db

# Brainstorm
.superpowers/
```

Guardar en `/home/krasorx/proyectos-personales/odoo-tailwind-css/.gitignore`

- [ ] **Step 2: Commit todo el código existente**

```bash
git add .
git commit -m "chore: initial commit — mrp_dashboard, custom_dashboards, docs"
```

- [ ] **Step 3: Crear repo en GitHub y pushear**

```bash
gh repo create krasorx/odoo-dashboards --public --description "Odoo Manufacturing dashboards — BOM multi-level and weekly MRP" --source . --remote origin --push
```

Resultado esperado: URL del repo en la consola, rama `master` publicada.

---

## Task 2: Scaffold del addon bom_dashboard

**Files:**
- Create: `bom_dashboard/__manifest__.py`
- Create: `bom_dashboard/__init__.py`
- Create: `bom_dashboard/controllers/__init__.py`
- Create: `bom_dashboard/security/ir.model.access.csv`
- Create: `bom_dashboard/views/bom_dashboard_menu.xml`

- [ ] **Step 1: Crear `bom_dashboard/__manifest__.py`**

```python
# -*- coding: utf-8 -*-
{
    'name': 'BOM Dashboard',
    'version': '19.0.1.0.0',
    'category': 'Manufacturing',
    'summary': 'Multi-level BOM dashboard with structure and active MOs views',
    'depends': ['mrp', 'web'],
    'data': [
        'security/ir.model.access.csv',
        'views/bom_dashboard_menu.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'bom_dashboard/static/src/js/components/bom_colors.js',
            'bom_dashboard/static/src/js/components/BomProductCard.js',
            'bom_dashboard/static/src/js/components/MoBomCard.js',
            'bom_dashboard/static/src/js/components/BomLevelColumn.js',
            'bom_dashboard/static/src/js/components/BomSidebar.js',
            'bom_dashboard/static/src/js/components/BomStructureView.js',
            'bom_dashboard/static/src/js/components/BomMoView.js',
            'bom_dashboard/static/src/js/components/BomDashboard.js',
            'bom_dashboard/static/src/js/bom_dashboard_action.js',
        ],
    },
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}
```

- [ ] **Step 2: Crear `bom_dashboard/__init__.py`**

```python
# -*- coding: utf-8 -*-
from . import controllers
```

- [ ] **Step 3: Crear `bom_dashboard/controllers/__init__.py`**

```python
# -*- coding: utf-8 -*-
from . import bom_dashboard_controller
```

- [ ] **Step 4: Crear `bom_dashboard/security/ir.model.access.csv`**

```
id,name,model_id:id,group_id:id,perm_read,perm_write,perm_create,perm_unlink
```

(Solo la cabecera — no hay modelos nuevos en este addon)

- [ ] **Step 5: Crear `bom_dashboard/views/bom_dashboard_menu.xml`**

```xml
<?xml version="1.0" encoding="utf-8"?>
<odoo>
    <record id="action_bom_dashboard_client" model="ir.actions.client">
        <field name="name">Dashboard BOM</field>
        <field name="tag">bom_dashboard.BomDashboard</field>
    </record>

    <menuitem
        id="menu_bom_dashboard"
        name="Dashboard BOM"
        parent="mrp.menu_mrp_root"
        action="action_bom_dashboard_client"
        groups="mrp.group_mrp_user"
        sequence="6"/>
</odoo>
```

- [ ] **Step 6: Commit**

```bash
git add bom_dashboard/
git commit -m "feat(bom_dashboard): scaffold addon — manifest, security, menu"
```

---

## Task 3: Controlador Python

**Files:**
- Create: `bom_dashboard/controllers/bom_dashboard_controller.py`

- [ ] **Step 1: Crear el controlador**

```python
# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request


class BomDashboardController(http.Controller):

    @http.route('/bom/dashboard/boms', type='json', auth='user', methods=['POST'])
    def get_boms(self):
        boms = request.env['mrp.bom'].sudo().search([('active', '=', True)])
        return [{'id': b.id, 'name': b.product_tmpl_id.name} for b in boms]

    @http.route('/bom/dashboard/data', type='json', auth='user', methods=['POST'])
    def get_bom_data(self, bom_id, state_filter=False):
        bom = request.env['mrp.bom'].sudo().browse(int(bom_id))
        if not bom.exists():
            return {'boms': self._get_boms(), 'tree': None}
        tree = self._expand_bom(bom, level=0, state_filter=state_filter,
                                visited=set(), parent_name=None)
        return {'boms': self._get_boms(), 'tree': tree}

    # ── Helpers ────────────────────────────────────────────────────────────────

    def _get_boms(self):
        boms = request.env['mrp.bom'].sudo().search([('active', '=', True)])
        return [{'id': b.id, 'name': b.product_tmpl_id.name} for b in boms]

    def _get_route_type(self, product):
        mfg_route = request.env.ref(
            'mrp.route_warehouse0_manufacture', raise_if_not_found=False)
        if mfg_route and mfg_route in product.route_ids:
            return 'manufacture'
        return 'buy'

    def _get_mos(self, product, state_filter):
        domain = [
            ('product_id', '=', product.id),
            ('state', 'not in', ['done', 'cancel']),
        ]
        if state_filter:
            domain.append(('state', '=', state_filter))
        productions = request.env['mrp.production'].sudo().search(domain)
        return [self._format_mo(p) for p in productions]

    def _format_mo(self, prod):
        user = prod.user_id
        return {
            'id': prod.id,
            'name': prod.name,
            'product_name': prod.product_id.display_name,
            'lot': prod.lot_producing_id.name or '',
            'qty_producing': prod.qty_producing,
            'product_qty': prod.product_qty,
            'state': prod.state,
            'responsible_name': user.name if user else '',
            'responsible_avatar': (
                f'/web/image/res.users/{user.id}/avatar_128' if user else ''
            ),
        }

    def _expand_bom(self, bom, level, state_filter, visited, parent_name):
        """Recursively expand a BOM into a tree node. Max depth: 10."""
        if bom.id in visited or level > 9:
            return None
        visited = visited | {bom.id}

        product = bom.product_id or bom.product_tmpl_id.product_variant_id
        route_type = self._get_route_type(product)
        mos = self._get_mos(product, state_filter) if route_type == 'manufacture' else []

        children = []
        for line in bom.bom_line_ids:
            child_product = line.product_id
            child_route_type = self._get_route_type(child_product)

            child_bom = request.env['mrp.bom'].sudo().search([
                ('product_tmpl_id', '=', child_product.product_tmpl_id.id),
                ('active', '=', True),
            ], limit=1)

            if child_bom and child_bom.id not in visited:
                # Recurse into child BOM
                child_node = self._expand_bom(
                    child_bom, level + 1, state_filter, visited, product.display_name)
                if child_node:
                    # Overlay BOM line qty (bom.product_qty may differ from line qty)
                    child_node['qty'] = line.product_qty
                    child_node['uom'] = line.product_uom_id.name
                    child_node['parent_name'] = product.display_name
                    children.append(child_node)
                    continue

            # Leaf node: no sub-BOM, or already visited (loop guard)
            child_mos = (
                self._get_mos(child_product, state_filter)
                if child_route_type == 'manufacture' else []
            )
            children.append({
                'level': level + 1,
                'product_id': child_product.id,
                'product_name': child_product.display_name,
                'product_ref': child_product.default_code or '',
                'qty': line.product_qty,
                'uom': line.product_uom_id.name,
                'has_bom': bool(child_bom),
                'route_type': child_route_type,
                'parent_name': product.display_name,
                'mos': child_mos,
                'children': [],
            })

        return {
            'level': level,
            'product_id': product.id,
            'product_name': product.display_name,
            'product_ref': product.default_code or '',
            'qty': bom.product_qty,
            'uom': bom.product_uom_id.name,
            'has_bom': True,
            'route_type': route_type,
            'parent_name': parent_name,
            'mos': mos,
            'children': children,
        }
```

- [ ] **Step 2: Verificar sintaxis Python**

```bash
python3 -c "import ast; ast.parse(open('bom_dashboard/controllers/bom_dashboard_controller.py').read()); print('OK')"
```

Resultado esperado: `OK`

- [ ] **Step 3: Commit**

```bash
git add bom_dashboard/controllers/bom_dashboard_controller.py
git commit -m "feat(bom_dashboard): add BOM tree controller with recursive expansion"
```

---

## Task 4: bom_colors.js — constantes de colores por nivel

**Files:**
- Create: `bom_dashboard/static/src/js/components/bom_colors.js`

- [ ] **Step 1: Crear el archivo**

```js
/** @odoo-module */

// Indexed by BOM level — last entry repeats for deeper levels
export const LEVEL_BADGES = [
    'bg-blue-100 text-blue-800',
    'bg-sky-100 text-sky-800',
    'bg-teal-100 text-teal-800',
    'bg-violet-100 text-violet-800',
    'bg-pink-100 text-pink-800',
];

export function levelBadge(level) {
    return LEVEL_BADGES[Math.min(level, LEVEL_BADGES.length - 1)];
}
```

- [ ] **Step 2: Commit**

```bash
git add bom_dashboard/static/src/js/components/bom_colors.js
git commit -m "feat(bom_dashboard): add level color constants"
```

---

## Task 5: BomProductCard

**Files:**
- Create: `bom_dashboard/static/src/js/components/BomProductCard.js`

- [ ] **Step 1: Crear el componente**

```js
/** @odoo-module */
import { Component, xml } from "@odoo/owl";

export class BomProductCard extends Component {
    static template = xml`
        <div t-att-class="cardClass">
            <!-- Header row -->
            <div class="flex items-center gap-2 px-3 py-2 border-b border-gray-100">
                <t t-if="isBought">
                    <span class="text-green-500 font-bold text-sm leading-none">✓</span>
                    <span class="text-xs font-semibold text-gray-400">Comprado</span>
                </t>
                <t t-else="">
                    <span class="text-xs font-semibold text-blue-600">fab.</span>
                    <t t-if="props.product.has_bom">
                        <span class="ml-auto text-xs font-bold text-blue-400 flex-shrink-0">tiene BOM →</span>
                    </t>
                </t>
            </div>
            <!-- Body -->
            <div class="px-3 py-2 space-y-1">
                <p class="text-xs font-bold text-gray-800 leading-snug" t-esc="props.product.product_name"/>
                <t t-if="props.product.product_ref">
                    <p class="text-xs font-mono text-gray-400 truncate" t-esc="props.product.product_ref"/>
                </t>
                <div class="flex items-center justify-between pt-1 mt-1 border-t border-gray-50">
                    <span class="text-xs text-gray-500 font-mono">
                        <t t-esc="props.product.qty"/>
                        <t t-esc="' ' + (props.product.uom or '')"/>
                    </span>
                </div>
            </div>
        </div>
    `;

    static props = { product: Object };

    get isBought() {
        return this.props.product.route_type === 'buy';
    }

    get cardClass() {
        return [
            'rounded-xl border overflow-hidden mb-2 bg-white transition-shadow cursor-default',
            this.isBought
                ? 'border-dashed border-gray-200 opacity-70'
                : 'border-gray-200 shadow-sm hover:shadow-md',
        ].join(' ');
    }
}
```

- [ ] **Step 2: Commit**

```bash
git add bom_dashboard/static/src/js/components/BomProductCard.js
git commit -m "feat(bom_dashboard): add BomProductCard component"
```

---

## Task 6: MoBomCard

**Files:**
- Create: `bom_dashboard/static/src/js/components/MoBomCard.js`

- [ ] **Step 1: Crear el componente**

```js
/** @odoo-module */
import { Component, xml } from "@odoo/owl";

const STATE_HEADER = {
    draft:     'bg-gray-400',
    confirmed: 'bg-sky-500',
    progress:  'bg-orange-500',
    to_close:  'bg-blue-600',
    done:      'bg-green-600',
    waiting:   'bg-red-600',
};

const STATE_BADGE = {
    draft:     'bg-gray-100 text-gray-600',
    confirmed: 'bg-sky-100 text-sky-700',
    progress:  'bg-orange-100 text-orange-700',
    to_close:  'bg-blue-100 text-blue-700',
    done:      'bg-green-100 text-green-700',
    waiting:   'bg-red-100 text-red-700',
};

const STATE_LABEL = {
    draft:     'Borrador',
    confirmed: 'Confirmada',
    progress:  'En Progreso',
    to_close:  'Por Cerrar',
    done:      'Hecha',
    waiting:   'Esperando Op.',
};

export class MoBomCard extends Component {
    static template = xml`
        <div class="rounded-xl border border-gray-100 shadow-sm bg-white overflow-hidden mb-2 hover:shadow-md transition-shadow cursor-default">
            <!-- Header: avatar + responsable -->
            <div t-att-class="headerClass">
                <div class="w-8 h-8 rounded-full bg-white/20 border-2 border-white/30 flex items-center justify-center flex-shrink-0 overflow-hidden">
                    <t t-if="props.mo.responsible_avatar">
                        <img t-att-src="props.mo.responsible_avatar" class="w-full h-full object-cover" t-att-alt="props.mo.responsible_name"/>
                    </t>
                    <t t-else="">
                        <span class="text-white font-bold text-xs select-none" t-esc="initials"/>
                    </t>
                </div>
                <span class="text-white font-bold text-xs leading-tight ml-2 truncate flex-1"
                      t-esc="props.mo.responsible_name or 'Sin asignar'"/>
            </div>
            <!-- Body -->
            <div class="px-3 py-2 space-y-1">
                <p class="text-xs font-mono text-gray-400 tracking-wide" t-esc="props.mo.name"/>
                <p class="text-sm font-semibold text-gray-800 leading-snug" t-esc="props.mo.product_name"/>
                <t t-if="props.mo.lot">
                    <p class="text-xs text-gray-400 flex items-center gap-1">
                        <span>🏷</span><span t-esc="props.mo.lot"/>
                    </p>
                </t>
                <div class="flex items-center justify-between pt-1 border-t border-gray-50 mt-1">
                    <span class="text-xs text-gray-500 font-mono">
                        <t t-esc="props.mo.qty_producing"/>/<t t-esc="props.mo.product_qty"/>
                    </span>
                    <span t-att-class="badgeClass" t-esc="stateLabel"/>
                </div>
            </div>
        </div>
    `;

    static props = { mo: Object };

    get headerClass() {
        const color = STATE_HEADER[this.props.mo.state] || 'bg-gray-400';
        return `flex items-center px-3 py-2 ${color}`;
    }

    get badgeClass() {
        const colors = STATE_BADGE[this.props.mo.state] || 'bg-gray-100 text-gray-600';
        return `inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium ${colors}`;
    }

    get stateLabel() {
        return STATE_LABEL[this.props.mo.state] || this.props.mo.state;
    }

    get initials() {
        return (this.props.mo.responsible_name || '?')
            .split(' ').slice(0, 2)
            .map(w => w[0] || '').join('').toUpperCase();
    }
}
```

- [ ] **Step 2: Commit**

```bash
git add bom_dashboard/static/src/js/components/MoBomCard.js
git commit -m "feat(bom_dashboard): add MoBomCard component"
```

---

## Task 7: BomLevelColumn

**Files:**
- Create: `bom_dashboard/static/src/js/components/BomLevelColumn.js`

La columna recibe `groups` = `[{parentName, items}]` y un prop `mode` (`'structure'` o `'mos'`). Renderiza el badge de nivel, los separadores de padre, y las cards apropiadas.

- [ ] **Step 1: Crear el componente**

```js
/** @odoo-module */
import { Component, xml } from "@odoo/owl";
import { levelBadge } from "./bom_colors";
import { BomProductCard } from "./BomProductCard";
import { MoBomCard } from "./MoBomCard";

export class BomLevelColumn extends Component {
    static template = xml`
        <div class="flex flex-col flex-shrink-0 min-w-[180px] max-w-[210px]">
            <!-- Column header -->
            <div class="mb-3 flex-shrink-0">
                <span t-att-class="'text-xs font-bold uppercase tracking-wide px-2.5 py-1 rounded-full inline-block ' + badgeClass">
                    Nivel <t t-esc="props.level"/>
                </span>
            </div>

            <!-- Groups -->
            <div class="flex-1">
                <t t-foreach="props.groups" t-as="group" t-key="group_index">
                    <!-- Parent separator: only shown when multiple groups exist -->
                    <t t-if="props.groups.length > 1 and group.parentName">
                        <div class="text-xs text-gray-400 font-semibold uppercase tracking-wide mb-1 mt-3 px-1 truncate select-none">
                            ← <t t-esc="group.parentName"/>
                        </div>
                    </t>

                    <!-- Structure mode: render BomProductCard for every item -->
                    <t t-if="props.mode === 'structure'">
                        <t t-foreach="group.items" t-as="item" t-key="item.product_id">
                            <BomProductCard product="item"/>
                        </t>
                    </t>

                    <!-- MOs mode: render MoBomCard per MO + BomProductCard for bought items -->
                    <t t-else="">
                        <t t-foreach="group.items" t-as="item" t-key="item.product_id">
                            <t t-if="item.route_type === 'buy'">
                                <BomProductCard product="item"/>
                            </t>
                            <t t-else="">
                                <t t-if="item.mos and item.mos.length">
                                    <t t-foreach="item.mos" t-as="mo" t-key="mo.id">
                                        <MoBomCard mo="mo"/>
                                    </t>
                                </t>
                                <t t-else="">
                                    <div class="text-gray-300 text-xs text-center py-4 border border-dashed border-gray-100 rounded-xl mb-2 select-none"
                                         t-esc="item.product_name + ' — sin MOs'"/>
                                </t>
                            </t>
                        </t>
                    </t>
                </t>

                <!-- Empty column -->
                <t t-if="isEmpty">
                    <div class="text-gray-300 text-xs text-center py-10 select-none"
                         t-esc="props.emptyText or 'Sin elementos'"/>
                </t>
            </div>
        </div>
    `;

    static components = { BomProductCard, MoBomCard };

    static props = {
        level: Number,
        groups: Array,
        mode: String,
        emptyText: { type: String, optional: true },
    };

    get badgeClass() {
        return levelBadge(this.props.level);
    }

    get isEmpty() {
        return this.props.groups.every(g => !g.items || g.items.length === 0);
    }
}
```

- [ ] **Step 2: Commit**

```bash
git add bom_dashboard/static/src/js/components/BomLevelColumn.js
git commit -m "feat(bom_dashboard): add BomLevelColumn with parent grouping and dual mode"
```

---

## Task 8: BomSidebar

**Files:**
- Create: `bom_dashboard/static/src/js/components/BomSidebar.js`

- [ ] **Step 1: Crear el componente**

```js
/** @odoo-module */
import { Component, useState, xml } from "@odoo/owl";

const STATE_OPTIONS = [
    { value: '',          label: 'Todos los estados' },
    { value: 'draft',     label: 'Borrador' },
    { value: 'confirmed', label: 'Confirmada' },
    { value: 'progress',  label: 'En Progreso' },
    { value: 'to_close',  label: 'Por Cerrar' },
    { value: 'waiting',   label: 'Esperando Op.' },
];

export class BomSidebar extends Component {
    static template = xml`
        <div class="bg-gray-900 flex-shrink-0 flex flex-col" style="width:200px;">
            <!-- Brand header -->
            <div class="px-3 py-3.5 border-b border-gray-700 flex-shrink-0">
                <span class="text-xs font-bold text-gray-100 tracking-wide">BOM Dashboard</span>
            </div>

            <!-- Search -->
            <div class="px-2.5 py-2 flex-shrink-0">
                <div class="bg-gray-700 rounded-md px-2.5 py-1.5 flex items-center gap-1.5">
                    <span class="text-gray-400 text-xs select-none">🔍</span>
                    <input
                        class="bg-transparent text-xs text-gray-200 placeholder-gray-500 outline-none w-full"
                        placeholder="Buscar BOM..."
                        t-on-input="onSearch"
                    />
                </div>
            </div>

            <!-- BOM list -->
            <div class="flex-1 overflow-y-auto px-2 py-1 min-h-0">
                <div class="text-gray-500 text-xs font-bold uppercase px-1.5 py-1 mb-1 tracking-wide">
                    Bills of Materials
                </div>
                <t t-foreach="filteredBoms" t-as="bom" t-key="bom.id">
                    <button
                        t-att-class="bomItemClass(bom.id)"
                        t-on-click="() => this.props.onSelect(bom.id)"
                    >
                        <span t-att-class="'w-1.5 h-1.5 rounded-full flex-shrink-0 ' + (props.selectedBomId === bom.id ? 'bg-blue-400' : 'bg-gray-600')"/>
                        <span class="truncate" t-esc="bom.name"/>
                    </button>
                </t>
                <t t-if="!filteredBoms.length">
                    <div class="text-gray-600 text-xs text-center py-6 select-none">Sin resultados</div>
                </t>
            </div>

            <!-- State filter — only visible in MOs tab -->
            <t t-if="props.activeTab === 'mos'">
                <div class="px-2.5 py-3 border-t border-gray-700 flex-shrink-0">
                    <div class="text-gray-500 text-xs font-bold uppercase mb-2 tracking-wide">Filtros</div>
                    <select
                        class="w-full bg-gray-700 border border-gray-600 rounded-md px-2 py-1.5 text-xs text-gray-300 outline-none focus:ring-1 focus:ring-blue-500 cursor-pointer"
                        t-on-change="onStateChange"
                    >
                        <t t-foreach="stateOptions" t-as="opt" t-key="opt.value">
                            <option
                                t-att-value="opt.value"
                                t-att-selected="props.stateFilter === opt.value"
                                t-esc="opt.label"
                            />
                        </t>
                    </select>
                </div>
            </t>
        </div>
    `;

    static props = {
        boms: Array,
        selectedBomId: { type: [Number, Boolean] },
        onSelect: Function,
        stateFilter: { type: [String, Boolean] },
        onStateFilter: Function,
        activeTab: String,
    };

    setup() {
        this.stateOptions = STATE_OPTIONS;
        this.local = useState({ search: '' });
    }

    get filteredBoms() {
        const q = this.local.search.toLowerCase().trim();
        if (!q) return this.props.boms;
        return this.props.boms.filter(b => b.name.toLowerCase().includes(q));
    }

    onSearch(ev) {
        this.local.search = ev.target.value;
    }

    onStateChange(ev) {
        this.props.onStateFilter(ev.target.value);
    }

    bomItemClass(id) {
        const active = this.props.selectedBomId === id;
        return [
            'w-full text-left flex items-center gap-2 px-2 py-1.5 rounded-md text-xs mb-0.5 transition-colors',
            active
                ? 'bg-blue-600 text-white font-bold'
                : 'text-gray-400 hover:bg-gray-700 hover:text-gray-200',
        ].join(' ');
    }
}
```

- [ ] **Step 2: Commit**

```bash
git add bom_dashboard/static/src/js/components/BomSidebar.js
git commit -m "feat(bom_dashboard): add BomSidebar with local search and state filter"
```

---

## Task 9: BomStructureView y BomMoView

**Files:**
- Create: `bom_dashboard/static/src/js/components/BomStructureView.js`
- Create: `bom_dashboard/static/src/js/components/BomMoView.js`

Ambas vistas reciben `columns` (ya filtradas por `visibleColumns`) y `hiddenCount`. Renderizan un `BomLevelColumn` por cada columna más el botón "Ver más" si `hiddenCount > 0`.

- [ ] **Step 1: Crear `BomStructureView.js`**

```js
/** @odoo-module */
import { Component, xml } from "@odoo/owl";
import { BomLevelColumn } from "./BomLevelColumn";

export class BomStructureView extends Component {
    static template = xml`
        <div class="overflow-x-auto h-full">
            <div class="flex gap-4 p-4 h-full items-start" style="min-width: max-content;">
                <t t-foreach="props.columns" t-as="col" t-key="col_index">
                    <BomLevelColumn
                        level="col_index"
                        groups="col"
                        mode="'structure'"
                        emptyText="'Sin productos'"
                    />
                    <!-- Arrow: show between columns and before "Ver más" -->
                    <t t-if="col_index !== props.columns.length - 1 or props.hiddenCount !== 0">
                        <div class="text-gray-300 text-xl self-start mt-7 flex-shrink-0">→</div>
                    </t>
                </t>

                <!-- Ver más button -->
                <t t-if="props.hiddenCount !== 0">
                    <div class="self-start mt-6 flex-shrink-0">
                        <button
                            class="text-xs font-semibold text-blue-500 border border-blue-200 rounded-full px-3 py-1.5 hover:bg-blue-50 transition-colors whitespace-nowrap"
                            t-on-click="() => this.props.onShowAll()"
                        >
                            Ver más niveles (+<t t-esc="props.hiddenCount"/>)
                        </button>
                    </div>
                </t>
            </div>
        </div>
    `;

    static components = { BomLevelColumn };

    static props = {
        columns: Array,
        hiddenCount: Number,
        onShowAll: Function,
    };
}
```

- [ ] **Step 2: Crear `BomMoView.js`**

```js
/** @odoo-module */
import { Component, xml } from "@odoo/owl";
import { BomLevelColumn } from "./BomLevelColumn";

export class BomMoView extends Component {
    static template = xml`
        <div class="overflow-x-auto h-full">
            <div class="flex gap-4 p-4 h-full items-start" style="min-width: max-content;">
                <t t-foreach="props.columns" t-as="col" t-key="col_index">
                    <BomLevelColumn
                        level="col_index"
                        groups="col"
                        mode="'mos'"
                        emptyText="'Sin MOs activas'"
                    />
                    <!-- Arrow: show between columns and before "Ver más" -->
                    <t t-if="col_index !== props.columns.length - 1 or props.hiddenCount !== 0">
                        <div class="text-gray-300 text-xl self-start mt-7 flex-shrink-0">→</div>
                    </t>
                </t>

                <!-- Ver más button -->
                <t t-if="props.hiddenCount !== 0">
                    <div class="self-start mt-6 flex-shrink-0">
                        <button
                            class="text-xs font-semibold text-blue-500 border border-blue-200 rounded-full px-3 py-1.5 hover:bg-blue-50 transition-colors whitespace-nowrap"
                            t-on-click="() => this.props.onShowAll()"
                        >
                            Ver más niveles (+<t t-esc="props.hiddenCount"/>)
                        </button>
                    </div>
                </t>

                <!-- Refresh indicator overlay -->
                <t t-if="props.loading">
                    <div class="fixed bottom-4 right-4 bg-white border border-gray-200 rounded-full px-3 py-1.5 shadow-sm flex items-center gap-1.5 text-xs text-gray-400">
                        <span class="animate-spin inline-block">↻</span>
                        <span>Actualizando...</span>
                    </div>
                </t>
            </div>
        </div>
    `;

    static components = { BomLevelColumn };

    static props = {
        columns: Array,
        hiddenCount: Number,
        onShowAll: Function,
        loading: Boolean,
    };
}
```

- [ ] **Step 3: Commit**

```bash
git add bom_dashboard/static/src/js/components/BomStructureView.js \
        bom_dashboard/static/src/js/components/BomMoView.js
git commit -m "feat(bom_dashboard): add BomStructureView and BomMoView tab components"
```

---

## Task 10: BomDashboard (root) + action

**Files:**
- Create: `bom_dashboard/static/src/js/components/BomDashboard.js`
- Create: `bom_dashboard/static/src/js/bom_dashboard_action.js`

- [ ] **Step 1: Crear `BomDashboard.js`**

```js
/** @odoo-module */
import { Component, useState, onMounted, onWillUnmount, xml } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";
import { BomSidebar } from "./BomSidebar";
import { BomStructureView } from "./BomStructureView";
import { BomMoView } from "./BomMoView";

export class BomDashboard extends Component {
    static template = xml`
        <div class="flex bg-gray-50 font-sans overflow-hidden" style="height:100vh;">

            <BomSidebar
                boms="state.boms"
                selectedBomId="state.selectedBomId"
                onSelect.bind="selectBom"
                stateFilter="state.stateFilter"
                onStateFilter.bind="setStateFilter"
                activeTab="state.activeTab"
            />

            <div class="flex-1 flex flex-col min-w-0 overflow-hidden">

                <!-- Tabs header -->
                <div class="bg-white border-b border-gray-200 px-4 flex items-center flex-shrink-0 shadow-sm" style="min-height:44px;">
                    <button t-att-class="tabClass('structure')" t-on-click="() => this.setTab('structure')">
                        📋 Estructura BOM
                    </button>
                    <button t-att-class="tabClass('mos')" t-on-click="() => this.setTab('mos')">
                        🏭 MOs Activas
                    </button>
                    <div class="ml-auto flex items-center gap-2 pr-1">
                        <t t-if="state.selectedBomId">
                            <span class="text-xs text-gray-500 font-semibold truncate max-w-xs" t-esc="selectedBomName"/>
                            <t t-if="state.activeTab === 'mos' and moCount > 0">
                                <span class="text-xs bg-amber-100 text-amber-800 px-2 py-0.5 rounded-full font-bold flex-shrink-0">
                                    <t t-esc="moCount"/> MOs
                                </span>
                            </t>
                            <t t-elif="state.activeTab === 'structure' and levelCount > 0">
                                <span class="text-xs bg-blue-100 text-blue-800 px-2 py-0.5 rounded-full font-bold flex-shrink-0">
                                    <t t-esc="levelCount"/> niveles
                                </span>
                            </t>
                        </t>
                        <t t-if="state.loading">
                            <span class="text-gray-400 text-xs animate-pulse ml-1">↻</span>
                        </t>
                    </div>
                </div>

                <!-- Content area -->
                <div class="flex-1 overflow-hidden">
                    <t t-if="!state.selectedBomId">
                        <div class="flex items-center justify-center h-full text-gray-300 text-sm select-none">
                            Seleccioná un BOM en el panel izquierdo
                        </div>
                    </t>
                    <t t-elif="state.loading and !state.bomTree">
                        <div class="flex items-center justify-center h-full text-gray-300 text-sm select-none animate-pulse">
                            Cargando...
                        </div>
                    </t>
                    <t t-elif="state.activeTab === 'structure'">
                        <BomStructureView
                            columns="visibleColumns"
                            hiddenCount="hiddenLevelsCount"
                            onShowAll.bind="showAllLevels"
                        />
                    </t>
                    <t t-else="">
                        <BomMoView
                            columns="visibleColumns"
                            hiddenCount="hiddenLevelsCount"
                            onShowAll.bind="showAllLevels"
                            loading="state.loading"
                        />
                    </t>
                </div>

            </div>
        </div>
    `;

    static components = { BomSidebar, BomStructureView, BomMoView };

    setup() {
        this.rpc = useService("rpc");
        this.state = useState({
            boms: [],
            selectedBomId: false,
            activeTab: 'structure',
            bomTree: null,
            stateFilter: false,
            showAll: false,
            loading: false,
        });
        this._timer = null;

        onMounted(async () => {
            this._injectTailwind();
            await this._loadBoms();
        });

        onWillUnmount(() => {
            if (this._timer) clearInterval(this._timer);
        });
    }

    _injectTailwind() {
        if (!document.querySelector('#bom-tw-cdn')) {
            const s = document.createElement('script');
            s.id = 'bom-tw-cdn';
            s.src = 'https://cdn.tailwindcss.com';
            document.head.appendChild(s);
        }
    }

    async _loadBoms() {
        const boms = await this.rpc('/bom/dashboard/boms', {});
        this.state.boms = boms || [];
        if (this.state.boms.length && !this.state.selectedBomId) {
            await this.selectBom(this.state.boms[0].id);
        }
    }

    async loadData() {
        if (!this.state.selectedBomId) return;
        this.state.loading = true;
        try {
            const result = await this.rpc('/bom/dashboard/data', {
                bom_id: this.state.selectedBomId,
                state_filter: this.state.stateFilter || false,
            });
            this.state.boms = result.boms || this.state.boms;
            this.state.bomTree = result.tree || null;
        } catch (err) {
            console.error('[BomDashboard] Error loading data:', err);
        } finally {
            this.state.loading = false;
        }
    }

    async selectBom(id) {
        this.state.selectedBomId = id;
        this.state.showAll = false;
        this.state.bomTree = null;
        if (this._timer) clearInterval(this._timer);
        await this.loadData();
        // Only auto-refresh in MOs tab
        this._timer = setInterval(() => {
            if (this.state.activeTab === 'mos') this.loadData();
        }, 30_000);
    }

    setTab(tab) {
        this.state.activeTab = tab;
    }

    setStateFilter(val) {
        this.state.stateFilter = val || false;
        this.loadData();
    }

    showAllLevels() {
        this.state.showAll = true;
    }

    tabClass(tab) {
        const active = this.state.activeTab === tab;
        return [
            'px-4 py-3 text-xs font-semibold border-b-2 transition-colors flex-shrink-0',
            active
                ? 'text-blue-600 border-blue-500'
                : 'text-gray-400 border-transparent hover:text-gray-600',
        ].join(' ');
    }

    get selectedBomName() {
        const bom = this.state.boms.find(b => b.id === this.state.selectedBomId);
        return bom ? bom.name : '';
    }

    // Flatten nested tree into columns: columns[level] = [{parentName, items}]
    get allColumns() {
        if (!this.state.bomTree) return [];
        const columns = [];

        const traverse = (node, parentName) => {
            const lvl = node.level;
            if (!columns[lvl]) columns[lvl] = [];
            let group = columns[lvl].find(g => g.parentName === parentName);
            if (!group) {
                group = { parentName, items: [] };
                columns[lvl].push(group);
            }
            group.items.push(node);
            for (const child of node.children || []) {
                traverse(child, node.product_name);
            }
        };

        traverse(this.state.bomTree, null);
        return columns;
    }

    get visibleColumns() {
        const all = this.allColumns;
        return this.state.showAll ? all : all.slice(0, 5);
    }

    get hiddenLevelsCount() {
        return Math.max(0, this.allColumns.length - 5);
    }

    get levelCount() {
        return this.allColumns.length;
    }

    get moCount() {
        if (!this.state.bomTree) return 0;
        let count = 0;
        const sum = (node) => {
            count += (node.mos || []).length;
            for (const c of node.children || []) sum(c);
        };
        sum(this.state.bomTree);
        return count;
    }
}
```

- [ ] **Step 2: Crear `bom_dashboard_action.js`**

```js
/** @odoo-module */
import { registry } from "@web/core/registry";
import { BomDashboard } from "./components/BomDashboard";

registry.category("actions").add("bom_dashboard.BomDashboard", BomDashboard);
```

- [ ] **Step 3: Commit**

```bash
git add bom_dashboard/static/src/js/components/BomDashboard.js \
        bom_dashboard/static/src/js/bom_dashboard_action.js
git commit -m "feat(bom_dashboard): add BomDashboard root component and action registration"
```

---

## Task 11: Push a GitHub

- [ ] **Step 1: Verificar estado del repo**

```bash
git log --oneline
git status
```

Resultado esperado: todos los commits del plan, working tree limpio.

- [ ] **Step 2: Push**

```bash
git push origin master
```

- [ ] **Step 3: Verificar en GitHub**

```bash
gh repo view krasorx/odoo-dashboards --web
```

Abre el browser con el repo. Verificar que los archivos del addon `bom_dashboard` están presentes.

---

## Task 12: Instalación y verificación manual

No hay tests automatizados para OWL en Odoo — la verificación es funcional en el browser.

- [ ] **Step 1: Instalar el addon en Odoo**

En `odoo.conf` o en la línea de comando, agregar `bom_dashboard` a los addons path. Luego en Odoo:

```
Settings > Activate developer mode
Apps > Update Apps List
Apps > Buscar "BOM Dashboard" > Install
```

- [ ] **Step 2: Verificar que el menú aparece**

En Manufacturing, debe aparecer el ítem "Dashboard BOM" (sequence 6, justo después de "Dashboard Semanal").

- [ ] **Step 3: Verificar ruta /bom/dashboard/boms**

En Odoo shell o browser DevTools:

```bash
# En odoo shell
import requests, json
r = requests.post('http://localhost:8069/bom/dashboard/boms',
    json={"jsonrpc":"2.0","method":"call","params":{}},
    cookies={"session_id": "<tu_session>"})
print(json.dumps(r.json(), indent=2))
```

Resultado esperado: lista de BOMs `[{"id": N, "name": "..."}]`.

- [ ] **Step 4: Verificar Tab "Estructura BOM"**

- Seleccioná un BOM en el sidebar → columnas aparecen con productos por nivel
- Productos manufacturados: borde sólido, badge "fab.", badge "tiene BOM →" si aplica
- Productos comprados: borde punteado, ✓ "Comprado"
- Si el BOM tiene >5 niveles: botón "Ver más niveles (+N)" aparece al final

- [ ] **Step 5: Verificar Tab "MOs Activas"**

- MOs aparecen con avatar del responsable, referencia, qty y badge de estado
- Comprados muestran ✓ card (no ocultos)
- Filtro "Estado" en el sidebar filtra las MOs en tiempo real
- Refresh automático cada 30s solo cuando el tab MOs está activo

- [ ] **Step 6: Verificar responsividad**

- En pantalla angosta: `overflow-x-auto` permite scroll horizontal de las columnas
- Sidebar permanece visible en pantalla

- [ ] **Step 7: Commit final**

```bash
git push origin master
```
