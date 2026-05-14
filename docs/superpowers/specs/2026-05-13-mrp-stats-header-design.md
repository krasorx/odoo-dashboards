# MRP Stats Header — Design Spec
Date: 2026-05-13

## Resumen

Nuevo addon `mrp_stats_header` para Odoo 19. Inyecta un banner de estadísticas en la vista lista existente de `mrp.production` (Órdenes de Manufactura) sin reemplazarla. El banner muestra 6 cards — una por estado — con el conteo de MOs filtrado por semana actual por defecto. Un toggle en la barra de filtros cambia entre "Esta semana" y "Todo el tiempo". Hacer clic en una card filtra la lista por ese estado.

---

## 1. Módulo

**Nombre técnico:** `mrp_stats_header`
**Versión:** `19.0.1.0.0`
**Dependencias:** `mrp`, `web`
**Menú:** ninguno — se inyecta en la vista lista estándar de `mrp.production`

---

## 2. Estructura de archivos

```
mrp_stats_header/
├── __manifest__.py
├── __init__.py
├── controllers/
│   ├── __init__.py
│   └── mrp_stats_controller.py
├── security/
│   └── ir.model.access.csv
├── views/
│   └── mrp_production_list_view.xml
└── static/src/
    ├── xml/
    │   └── mrp_stats_list_controller.xml
    └── js/
        ├── mrp_stats_list_view.js
        ├── mrp_stats_list_controller.js
        └── components/
            ├── MrpStatsBanner.js
            └── MrpStatsCard.js
```

---

## 3. Diseño de interfaz

### Layout

```
┌──────────────────────────────────────────────────────────────┐
│ [Órdenes de Manufactura]   [Buscar…]  [📅 Esta semana | Todo]│  ← barra de filtros Odoo
├──────────────────────────────────────────────────────────────┤
│  Borrador  │ Confirmada │ En Progreso │ Por Cerrar │ Espera  │ Hecha │  ← banner
│     3      │     5      │      7      │     2      │    1    │   12  │
├──────────────────────────────────────────────────────────────┤
│ ☐  WH/MO/00042  Mesa de madera   En Progreso   12/05        │  ← lista estándar Odoo
│ ☐  WH/MO/00043  Silla           Confirmada    13/05        │
│ …                                                            │
└──────────────────────────────────────────────────────────────┘
```

### Toggle "Esta semana / Todo"

- Pill toggle en el slot de acciones adicionales del control panel (derecha, junto a los botones de vista)
- Estado por defecto: **"Esta semana"** (lunes 00:00 → domingo 23:59 de la semana en curso)
- Al cambiar a **"Todo"**: sin filtro de fecha, cuenta todas las MOs no canceladas
- El toggle **solo cambia los números de las cards**; no filtra la lista de Odoo

### Cards de estado

- 6 cards en fila horizontal, `overflow-x: auto` si la pantalla es angosta
- Cada card: número grande + etiqueta corta en mayúsculas
- Colores por estado (iguales a los del `MoCard` existente en `mrp_dashboard`):

| Estado | Clave | Color borde | Color número |
|--------|-------|------------|--------------|
| Borrador | `draft` | `border-gray-200` | `text-gray-600` |
| Confirmada | `confirmed` | `border-sky-200` | `text-sky-700` |
| En Progreso | `progress` | `border-orange-200` | `text-orange-700` |
| Por Cerrar | `to_close` | `border-blue-200` | `text-blue-700` |
| Esperando Op. | `waiting` | `border-red-200` | `text-red-700` |
| Hecha | `done` | `border-green-200` | `text-green-700` |

- Estado `cancel` no se muestra
- Card **activa** (filtro aplicado): fondo coloreado + borde 2px sólido + resto de cards con `opacity-40`
- Card **inactiva**: fondo blanco, borde 1px, opacidad normal

### Comportamiento de clic (filtro de lista)

- Clic en una card inactiva → aplica dominio `[('state', '=', state)]` al modelo de lista
- Clic en la card activa → quita el filtro (vuelve al dominio base)
- Solo un estado activo a la vez
- El filtro de estado es adicional al dominio base de la vista (no lo reemplaza)

---

## 4. Componentes OWL

### `MrpProductionListController` (extiende `ListController`)

**Estado adicional:**
```js
{
  scope: 'week',        // 'week' | 'all'
  activeState: null,    // string | null — estado activo para filtrar lista
  counts: {             // conteos por estado
    draft: 0, confirmed: 0, progress: 0,
    to_close: 0, waiting: 0, done: 0,
  },
  statsLoading: false,
}
```

**Métodos adicionales:**
- `loadStats()` — POST `/mrp/stats/counts` con `{ scope }`, actualiza `counts`
- `setScope(scope)` — cambia `scope`, llama `loadStats()`
- `toggleStateFilter(state)` — alterna `activeState`; actualiza el dominio del modelo de lista via `this.model.load({ domain: [...] })`
- `get extraDomain()` — retorna `[('state','=', activeState)]` o `[]`

**Ciclo de vida:** `onMounted` → llama `loadStats()`.

**Template:** hereda `web.ListController` via `t-inherit` en el archivo XML. Añade:
1. Slot `control-panel-additional-actions`: el toggle pill "Esta semana / Todo"
2. Antes del renderer: `<MrpStatsBanner .../>`

### `MrpStatsBanner`

Props: `{ counts: Object, activeState: String|null, onCardClick: Function }`

Renderiza 6 `MrpStatsCard` en fila. No tiene estado propio.

### `MrpStatsCard`

Props: `{ state: String, count: Number, label: String, active: Boolean, onClick: Function }`

Renderiza una card individual. Clases CSS determinadas por `state` y `active`.

### `mrp_stats_list_view.js`

```js
import { listView } from "@web/views/list/list_view";
import { registry } from "@web/core/registry";
import { MrpProductionListController } from "./mrp_stats_list_controller";

registry.category("views").add("mrp_production_list", {
    ...listView,
    Controller: MrpProductionListController,
});
```

---

## 5. Controller Python

**Ruta:** `POST /mrp/stats/counts`
**Auth:** `user`

**Request:**
```json
{ "scope": "week" }
```

**Response:**
```json
{ "draft": 3, "confirmed": 5, "progress": 7, "to_close": 2, "waiting": 1, "done": 12 }
```

**Lógica:**
1. Si `scope == 'week'`: calcula inicio de semana (lunes 00:00) y fin (domingo 23:59) de la semana actual en la timezone del usuario
2. Construye dominio base: `[('state', 'not in', ['cancel'])]` + filtro de fecha si aplica
3. Llama `read_group(domain, ['state'], ['state'])` en `mrp.production`
4. Mapea resultado a dict `{ state: count }`; completa con 0 los estados sin resultados

---

## 6. Vista XML

### `mrp_production_list_view.xml`

Hereda la vista lista de `mrp.production` para añadir `js_class`:

```xml
<record id="mrp_production_list_view_stats" model="ir.ui.view">
    <field name="name">mrp.production.list.stats</field>
    <field name="model">mrp.production</field>
    <field name="inherit_id" ref="mrp.mrp_production_action_picking_datas"/>
    <field name="arch" type="xml">
        <list position="attributes">
            <attribute name="js_class">mrp_production_list</attribute>
        </list>
    </field>
</record>
```

> Nota: el `inherit_id` referencia la acción/vista lista estándar de `mrp.production`. Si el `ref` exacto difiere en la instalación, se ajusta al `id` correcto de la vista lista.

### `mrp_stats_list_controller.xml`

Template OWL que hereda `web.ListController` para añadir el toggle y el banner:

```xml
<templates>
    <t t-name="mrp_stats_header.MrpProductionListController"
       t-inherit="web.ListController"
       t-inherit-mode="extension">

        <!-- Toggle en el slot de acciones del control panel -->
        <xpath expr="//Layout" position="inside">
            <t t-set-slot="control-panel-additional-actions">
                <div class="d-flex align-items-center gap-1">
                    <div class="btn-group btn-group-sm">
                        <button t-att-class="scope === 'week' ? 'btn btn-primary' : 'btn btn-outline-secondary'"
                                t-on-click="() => this.setScope('week')">📅 Esta semana</button>
                        <button t-att-class="scope === 'all' ? 'btn btn-primary' : 'btn btn-outline-secondary'"
                                t-on-click="() => this.setScope('all')">Todo</button>
                    </div>
                </div>
            </t>
        </xpath>

        <!-- Banner antes del renderer -->
        <xpath expr="//t[@t-component='props.Renderer']" position="before">
            <MrpStatsBanner
                counts="state.counts"
                activeState="state.activeState"
                onCardClick.bind="toggleStateFilter"
            />
        </xpath>
    </t>
</templates>
```

---

## 7. Integración con el repo

El addon se ubica en:
```
odoo-dashboards/
├── mrp_dashboard/
├── bom_dashboard/
├── mrp_stats_header/     ← nuevo
└── docs/
```

---

## 8. Fuera de scope

- Auto-refresh automático de los conteos
- Multiselección de estados (solo un filtro activo a la vez)
- Filtro por equipo MRP o responsable en el banner
- Persistencia del scope seleccionado entre sesiones
- Exportación de los conteos
