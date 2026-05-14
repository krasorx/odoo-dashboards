# MRP Stats Header Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Crear el addon `mrp_stats_header` que inyecta un banner de conteos por estado sobre la vista lista estándar de `mrp.production`, con toggle semana/todo y filtro de lista al hacer clic en una card.

**Architecture:** Subclase de `ListController` de Odoo registrada como tipo de vista `mrp_production_list` vía `js_class`. El `post_init_hook` encuentra la vista lista base de `mrp.production` en runtime y le aplica herencia para agregar `js_class`. El banner de stats es un componente OWL independiente que vive en el template heredado del controller. Un controller Python expone `POST /mrp/stats/counts` con agrupación por estado y filtro de semana opcional.

**Tech Stack:** Odoo 19, OWL 2, Tailwind CSS CDN (mismo patrón que `mrp_dashboard`), Python 3

---

## File Map

| Archivo | Responsabilidad |
|---|---|
| `mrp_stats_header/__manifest__.py` | Metadatos, assets JS/XML, `post_init_hook` |
| `mrp_stats_header/__init__.py` | Importa `controllers`; define `post_init_hook` |
| `mrp_stats_header/controllers/__init__.py` | Importa el controller |
| `mrp_stats_header/controllers/mrp_stats_controller.py` | `POST /mrp/stats/counts` — `read_group` con filtro de fecha |
| `mrp_stats_header/security/ir.model.access.csv` | Header vacío (no hay modelos nuevos) |
| `mrp_stats_header/static/src/xml/mrp_stats_list_controller.xml` | Template OWL que hereda `web.ListController` — añade banner |
| `mrp_stats_header/static/src/js/components/MrpStatsCard.js` | Card individual de un estado |
| `mrp_stats_header/static/src/js/components/MrpStatsBanner.js` | Fila de 6 cards + toggle semana/todo |
| `mrp_stats_header/static/src/js/mrp_stats_list_controller.js` | Extiende `ListController`; carga stats; aplica dominio |
| `mrp_stats_header/static/src/js/mrp_stats_list_view.js` | Registra el tipo de vista `mrp_production_list` |

---

## Task 1: Scaffold del addon

**Files:**
- Create: `mrp_stats_header/__manifest__.py`
- Create: `mrp_stats_header/__init__.py`
- Create: `mrp_stats_header/controllers/__init__.py`
- Create: `mrp_stats_header/security/ir.model.access.csv`

- [ ] **Step 1: Crear `mrp_stats_header/__manifest__.py`**

```python
# -*- coding: utf-8 -*-
{
    'name': 'MRP Stats Header',
    'version': '19.0.1.0.0',
    'category': 'Manufacturing',
    'summary': 'Stats banner on the manufacturing orders list view — counts by state with week filter',
    'depends': ['mrp', 'web'],
    'data': [
        'security/ir.model.access.csv',
    ],
    'assets': {
        'web.assets_backend': [
            'mrp_stats_header/static/src/xml/mrp_stats_list_controller.xml',
            'mrp_stats_header/static/src/js/components/MrpStatsCard.js',
            'mrp_stats_header/static/src/js/components/MrpStatsBanner.js',
            'mrp_stats_header/static/src/js/mrp_stats_list_controller.js',
            'mrp_stats_header/static/src/js/mrp_stats_list_view.js',
        ],
    },
    'post_init_hook': 'post_init_hook',
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}
```

- [ ] **Step 2: Crear `mrp_stats_header/__init__.py`**

```python
# -*- coding: utf-8 -*-
from . import controllers


def post_init_hook(env):
    """Find the base mrp.production list view and add js_class to it."""
    base_view = env['ir.ui.view'].search([
        ('model', '=', 'mrp.production'),
        ('type', '=', 'list'),
        ('inherit_id', '=', False),
    ], order='priority asc', limit=1)

    if not base_view:
        return

    # Avoid creating duplicate if already installed
    existing = env['ir.ui.view'].search([
        ('name', '=', 'mrp.production.list.stats.jsclass'),
        ('model', '=', 'mrp.production'),
    ])
    if existing:
        return

    env['ir.ui.view'].sudo().create({
        'name': 'mrp.production.list.stats.jsclass',
        'model': 'mrp.production',
        'type': 'list',
        'inherit_id': base_view.id,
        'arch_base': (
            '<list position="attributes">'
            '<attribute name="js_class">mrp_production_list</attribute>'
            '</list>'
        ),
    })
```

- [ ] **Step 3: Crear `mrp_stats_header/controllers/__init__.py`**

```python
# -*- coding: utf-8 -*-
from . import mrp_stats_controller
```

- [ ] **Step 4: Crear `mrp_stats_header/security/ir.model.access.csv`**

```
id,name,model_id:id,group_id:id,perm_read,perm_write,perm_create,perm_unlink
```

(Solo la cabecera — no hay modelos nuevos)

- [ ] **Step 5: Verificar sintaxis Python**

```bash
cd /home/krasorx/proyectos-personales/odoo-tailwind-css
python3 -c "import ast; ast.parse(open('mrp_stats_header/__init__.py').read()); print('OK')"
python3 -c "import ast; ast.parse(open('mrp_stats_header/__manifest__.py').read()); print('OK')"
```

Resultado esperado: `OK` para cada archivo.

- [ ] **Step 6: Commit**

```bash
git add mrp_stats_header/
git commit -m "feat(mrp_stats_header): scaffold addon — manifest, security, post_init_hook"
```

---

## Task 2: Controller Python

**Files:**
- Create: `mrp_stats_header/controllers/mrp_stats_controller.py`

- [ ] **Step 1: Crear el controller**

```python
# -*- coding: utf-8 -*-
from datetime import datetime, timedelta
from odoo import http
from odoo.http import request

STATES = ['draft', 'confirmed', 'progress', 'to_close', 'waiting', 'done']


class MrpStatsController(http.Controller):

    @http.route('/mrp/stats/counts', type='json', auth='user', methods=['POST'])
    def get_counts(self, scope='week'):
        domain = [('state', 'not in', ['cancel'])]

        if scope == 'week':
            today = datetime.utcnow()
            monday = today - timedelta(days=today.weekday())
            monday = monday.replace(hour=0, minute=0, second=0, microsecond=0)
            sunday = monday + timedelta(days=6)
            sunday = sunday.replace(hour=23, minute=59, second=59)
            domain += [
                ('date_start', '>=', monday.strftime('%Y-%m-%d %H:%M:%S')),
                ('date_start', '<=', sunday.strftime('%Y-%m-%d %H:%M:%S')),
            ]

        groups = request.env['mrp.production'].sudo().read_group(
            domain=domain,
            fields=['state'],
            groupby=['state'],
        )

        result = {s: 0 for s in STATES}
        for g in groups:
            state = g.get('state')
            if state in result:
                result[state] = g.get('state_count', 0)
        return result
```

- [ ] **Step 2: Verificar sintaxis Python**

```bash
python3 -c "import ast; ast.parse(open('mrp_stats_header/controllers/mrp_stats_controller.py').read()); print('OK')"
```

Resultado esperado: `OK`

- [ ] **Step 3: Commit**

```bash
git add mrp_stats_header/controllers/mrp_stats_controller.py
git commit -m "feat(mrp_stats_header): add stats counts controller"
```

---

## Task 3: MrpStatsCard

**Files:**
- Create: `mrp_stats_header/static/src/js/components/MrpStatsCard.js`

- [ ] **Step 1: Crear el componente**

```js
/** @odoo-module */
import { Component, xml } from "@odoo/owl";

// Matches STATE_BADGE and STATE_HEADER colors from mrp_dashboard/MoCard.js
const CARD_COLORS = {
    draft:     { border: 'border-gray-200',   text: 'text-gray-600',   activeBg: 'bg-gray-100' },
    confirmed: { border: 'border-sky-200',    text: 'text-sky-700',    activeBg: 'bg-sky-50'   },
    progress:  { border: 'border-orange-200', text: 'text-orange-700', activeBg: 'bg-orange-50' },
    to_close:  { border: 'border-blue-200',   text: 'text-blue-700',   activeBg: 'bg-blue-50'  },
    waiting:   { border: 'border-red-200',    text: 'text-red-700',    activeBg: 'bg-red-50'   },
    done:      { border: 'border-green-200',  text: 'text-green-700',  activeBg: 'bg-green-50' },
};

export class MrpStatsCard extends Component {
    static template = xml`
        <button
            t-att-class="cardClass"
            t-on-click="() => props.onClick(props.state)"
            type="button"
        >
            <span t-att-class="'text-2xl font-extrabold leading-none ' + colors.text"
                  t-esc="props.count"/>
            <span class="text-xs font-semibold uppercase tracking-wide text-gray-400 mt-0.5"
                  t-esc="props.label"/>
        </button>
    `;

    static props = {
        state: String,
        count: Number,
        label: String,
        active: Boolean,
        onClick: Function,
    };

    get colors() {
        return CARD_COLORS[this.props.state] || CARD_COLORS.draft;
    }

    get cardClass() {
        const c = this.colors;
        if (this.props.active) {
            return [
                'flex flex-col items-center justify-center px-4 py-3 rounded-xl',
                'border-2 transition-all duration-150 cursor-pointer select-none min-w-[90px]',
                c.activeBg, c.border, 'shadow-sm',
            ].join(' ');
        }
        return [
            'flex flex-col items-center justify-center px-4 py-3 rounded-xl',
            'border border-gray-100 bg-white transition-all duration-150',
            'cursor-pointer select-none min-w-[90px]',
            'hover:border-gray-200 hover:shadow-sm',
        ].join(' ');
    }
}
```

- [ ] **Step 2: Commit**

```bash
git add mrp_stats_header/static/src/js/components/MrpStatsCard.js
git commit -m "feat(mrp_stats_header): add MrpStatsCard component"
```

---

## Task 4: MrpStatsBanner

**Files:**
- Create: `mrp_stats_header/static/src/js/components/MrpStatsBanner.js`

- [ ] **Step 1: Crear el componente**

```js
/** @odoo-module */
import { Component, xml } from "@odoo/owl";
import { MrpStatsCard } from "./MrpStatsCard";

const CARD_DEFS = [
    { state: 'draft',     label: 'Borrador'    },
    { state: 'confirmed', label: 'Confirmada'  },
    { state: 'progress',  label: 'En Progreso' },
    { state: 'to_close',  label: 'Por Cerrar'  },
    { state: 'waiting',   label: 'Esperando'   },
    { state: 'done',      label: 'Hecha'       },
];

export class MrpStatsBanner extends Component {
    static template = xml`
        <div class="flex items-center gap-3 px-4 py-2 bg-gray-50 border-b border-gray-200 overflow-x-auto flex-shrink-0">
            <!-- Cards: inactive ones dim to opacity-40 when any card is active -->
            <div class="flex items-center gap-2 flex-1">
                <t t-foreach="cardDefs" t-as="def" t-key="def.state">
                    <div t-att-class="props.activeState and props.activeState !== def.state ? 'opacity-40 transition-opacity' : 'transition-opacity'">
                        <MrpStatsCard
                            state="def.state"
                            count="props.counts[def.state] || 0"
                            label="def.label"
                            active="props.activeState === def.state"
                            onClick="props.onCardClick"
                        />
                    </div>
                </t>
            </div>

            <!-- Toggle semana / todo -->
            <div class="flex-shrink-0 flex bg-gray-200 rounded-full p-0.5 ml-2">
                <button
                    t-att-class="scopeBtnClass('week')"
                    t-on-click="() => props.onScopeChange('week')"
                    type="button"
                >
                    📅 Esta semana
                </button>
                <button
                    t-att-class="scopeBtnClass('all')"
                    t-on-click="() => props.onScopeChange('all')"
                    type="button"
                >
                    Todo
                </button>
            </div>
        </div>
    `;

    static components = { MrpStatsCard };

    static props = {
        counts: Object,
        activeState: { type: [String, Boolean] },
        scope: String,
        onCardClick: Function,
        onScopeChange: Function,
    };

    setup() {
        this.cardDefs = CARD_DEFS;
    }

    scopeBtnClass(scope) {
        const active = this.props.scope === scope;
        return [
            'rounded-full px-3 py-1 text-xs font-semibold transition-colors whitespace-nowrap',
            active
                ? 'bg-white text-blue-700 shadow-sm'
                : 'text-gray-500 hover:text-gray-700',
        ].join(' ');
    }
}
```

- [ ] **Step 2: Commit**

```bash
git add mrp_stats_header/static/src/js/components/MrpStatsBanner.js
git commit -m "feat(mrp_stats_header): add MrpStatsBanner component with scope toggle"
```

---

## Task 5: MrpProductionListController + OWL template

**Files:**
- Create: `mrp_stats_header/static/src/js/mrp_stats_list_controller.js`
- Create: `mrp_stats_header/static/src/xml/mrp_stats_list_controller.xml`

- [ ] **Step 1: Crear `mrp_stats_list_controller.js`**

```js
/** @odoo-module */
import { ListController } from "@web/views/list/list_controller";
import { useState, onMounted } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";
import { MrpStatsBanner } from "./components/MrpStatsBanner";

export class MrpProductionListController extends ListController {
    static template = "mrp_stats_header.MrpProductionListController";
    static components = {
        ...ListController.components,
        MrpStatsBanner,
    };

    setup() {
        super.setup();
        this.rpc = useService("rpc");
        this.statsState = useState({
            scope: 'week',
            activeState: false,
            counts: {
                draft: 0, confirmed: 0, progress: 0,
                to_close: 0, waiting: 0, done: 0,
            },
        });

        onMounted(() => {
            this._injectTailwind();
            this.loadStats();
        });
    }

    // Dev-only: Tailwind CDN for rapid iteration. For production, replace with
    // a compiled CSS asset shipped in web.assets_backend instead of this script.
    _injectTailwind() {
        if (!document.querySelector('#mrp-stats-tw-cdn')) {
            const s = document.createElement('script');
            s.id = 'mrp-stats-tw-cdn';
            s.src = 'https://cdn.tailwindcss.com';
            document.head.appendChild(s);
        }
    }

    async loadStats() {
        try {
            const counts = await this.rpc('/mrp/stats/counts', {
                scope: this.statsState.scope,
            });
            this.statsState.counts = counts;
        } catch (e) {
            console.error('[MrpStatsHeader] Error loading stats:', e);
        }
    }

    setScope(scope) {
        this.statsState.scope = scope;
        this.loadStats();
    }

    async toggleStateFilter(state) {
        const isActive = this.statsState.activeState === state;
        this.statsState.activeState = isActive ? false : state;

        // Base domain from the action (does not include search-bar filters).
        // Combining with state filter is intentional: clicking a card is a
        // focused drill-down that replaces any current search-model domain.
        const base = this.props.domain || [];
        const extra = this.statsState.activeState
            ? [['state', '=', this.statsState.activeState]]
            : [];

        await this.model.load({ domain: [...base, ...extra] });
    }
}
```

- [ ] **Step 2: Crear `mrp_stats_list_controller.xml`**

```xml
<?xml version="1.0" encoding="UTF-8"?>
<templates xml:space="preserve">
    <t t-name="mrp_stats_header.MrpProductionListController"
       t-inherit="web.ListController"
       t-inherit-mode="extension">

        <!--
            Inject MrpStatsBanner before the list renderer.
            XPath targets the dynamic renderer tag in web.ListController.
            If Odoo upgrades change the template structure, verify with:
                grep -r "t-component.*Renderer" $(find . -path "*/web/static/src/views/list*")
        -->
        <xpath expr="//t[@t-component='props.Renderer']" position="before">
            <MrpStatsBanner
                counts="statsState.counts"
                activeState="statsState.activeState"
                scope="statsState.scope"
                onCardClick.bind="toggleStateFilter"
                onScopeChange.bind="setScope"
            />
        </xpath>
    </t>
</templates>
```

- [ ] **Step 3: Verificar sintaxis Python y estructura de directorios**

```bash
ls mrp_stats_header/static/src/xml/
ls mrp_stats_header/static/src/js/components/
```

Resultado esperado:
```
mrp_stats_list_controller.xml
MrpStatsCard.js  MrpStatsBanner.js
```

- [ ] **Step 4: Commit**

```bash
git add mrp_stats_header/static/src/js/mrp_stats_list_controller.js \
        mrp_stats_header/static/src/xml/mrp_stats_list_controller.xml
git commit -m "feat(mrp_stats_header): add MrpProductionListController with stats banner"
```

---

## Task 6: Registrar el tipo de vista

**Files:**
- Create: `mrp_stats_header/static/src/js/mrp_stats_list_view.js`

Este archivo combina el `ListController` personalizado con el `ListView` base de Odoo y lo registra bajo la clave `mrp_production_list`. El `post_init_hook` (ya en `__init__.py`) aplica `js_class="mrp_production_list"` a la vista lista de `mrp.production` en runtime.

- [ ] **Step 1: Crear `mrp_stats_list_view.js`**

```js
/** @odoo-module */
import { registry } from "@web/core/registry";
import { listView } from "@web/views/list/list_view";
import { MrpProductionListController } from "./mrp_stats_list_controller";

registry.category("views").add("mrp_production_list", {
    ...listView,
    Controller: MrpProductionListController,
});
```

- [ ] **Step 2: Verificar que el manifest lista todos los assets en orden correcto**

Abrir `mrp_stats_header/__manifest__.py` y confirmar que el orden en `web.assets_backend` es:
1. `mrp_stats_list_controller.xml` (template XML primero)
2. `MrpStatsCard.js`
3. `MrpStatsBanner.js`
4. `mrp_stats_list_controller.js`
5. `mrp_stats_list_view.js` (registro al final)

El orden importa porque cada archivo importa el anterior. El manifest ya fue escrito así en Task 1 — solo confirmar visualmente.

- [ ] **Step 3: Verificar sintaxis Python del __init__.py completo**

```bash
python3 -c "import ast; ast.parse(open('mrp_stats_header/__init__.py').read()); print('OK')"
```

Resultado esperado: `OK`

- [ ] **Step 4: Commit**

```bash
git add mrp_stats_header/static/src/js/mrp_stats_list_view.js
git commit -m "feat(mrp_stats_header): register mrp_production_list view type"
```

---

## Task 7: Push a GitHub y verificación manual

- [ ] **Step 1: Verificar estado del repo**

```bash
git log --oneline
git status
```

Resultado esperado: 6 commits del plan de `mrp_stats_header` más los commits previos. Working tree limpio.

- [ ] **Step 2: Push**

```bash
git push origin master
```

- [ ] **Step 3: Instalar el addon en Odoo**

En Odoo (con modo desarrollador activo):
```
Apps → Actualizar lista de aplicaciones
Apps → Buscar "MRP Stats Header" → Instalar
```

El `post_init_hook` se ejecuta automáticamente al instalar e inyecta `js_class` en la vista lista de `mrp.production`.

- [ ] **Step 4: Verificar el banner**

Navegar a Manufacturing → Órdenes de Manufactura (vista lista).

Verificar:
- El banner aparece entre la barra de búsqueda y las filas de la lista
- Se muestran 6 cards: Borrador, Confirmada, En Progreso, Por Cerrar, Esperando, Hecha
- Los números cambian al hacer clic en "Esta semana" vs "Todo"

- [ ] **Step 5: Verificar filtrado de lista**

- Hacer clic en una card (ej. "En Progreso") → la lista se filtra mostrando solo MOs en ese estado, la card se resalta
- Hacer clic en la misma card → el filtro se quita, la lista vuelve a mostrar todas

- [ ] **Step 6: Verificar ruta del controller**

En el DevTools del browser (Network tab):
- Al cargar la página y al cambiar el toggle, debe aparecer un POST a `/mrp/stats/counts`
- La respuesta debe ser un JSON con 6 claves: `draft`, `confirmed`, `progress`, `to_close`, `waiting`, `done`

- [ ] **Step 7: Si el banner no aparece — troubleshooting del js_class**

Si el banner no se muestra, verificar que el `post_init_hook` creó la vista heredada:

```python
# En Odoo shell
env['ir.ui.view'].search([('name', '=', 'mrp.production.list.stats.jsclass')]).read(['arch_base', 'inherit_id'])
```

Si no existe, ejecutar manualmente:
```python
from odoo.addons.mrp_stats_header import post_init_hook
post_init_hook(env)
env.cr.commit()
```

Y recargar la página.
