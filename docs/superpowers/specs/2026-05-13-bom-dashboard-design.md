# BOM Dashboard — Design Spec
Date: 2026-05-13

## Resumen

Nuevo addon `bom_dashboard` para Odoo 19. Proporciona dos vistas complementarias organizadas por estructura de BOM:
1. **Estructura BOM** — árbol de productos y cantidades por nivel, sin datos de MOs
2. **MOs Activas** — árbol de órdenes de manufactura activas organizadas por nivel de BOM

Ambas vistas comparten un sidebar lateral con la lista de BOMs. El addon se integra al módulo Manufacturing y usa OWL + Tailwind CSS (CDN), siguiendo los patrones del addon `mrp_dashboard` existente.

---

## 1. Módulo

**Nombre técnico:** `bom_dashboard`
**Versión:** `19.0.1.0.0`
**Dependencias:** `mrp`, `web`
**Menú:** dentro del módulo Manufacturing (hereda `mrp.menu_mrp_root`)

---

## 2. Estructura de archivos

```
bom_dashboard/
├── __manifest__.py
├── __init__.py
├── controllers/
│   ├── __init__.py
│   └── bom_dashboard_controller.py
├── security/
│   └── ir.model.access.csv
├── views/
│   └── bom_dashboard_menu.xml
└── static/src/
    └── js/
        ├── bom_dashboard_action.js
        └── components/
            ├── BomDashboard.js      # Root: sidebar + tabs + estado global
            ├── BomSidebar.js        # Lista de BOMs con buscador
            ├── BomStructureView.js  # Tab 1: columnas de productos BOM
            ├── BomMoView.js         # Tab 2: columnas de MOs activas
            ├── BomLevelColumn.js    # Columna de un nivel (compartida)
            ├── BomProductCard.js    # Card de producto en vista estructura
            └── MoBomCard.js         # Card de MO en vista MOs activas
```

---

## 3. Diseño de interfaz

### Layout general

```
┌─────────────────────────────────────────────────────────────┐
│ Sidebar (200px)          │ Header: tabs + info BOM activo    │
│ ─────────────────────    │ ─────────────────────────────────  │
│ [BOM Dashboard]          │ [📋 Estructura BOM] [🏭 MOs Act.]  │
│ 🔍 Buscar BOM...         │                                   │
│                          │  Nivel 0    →  Nivel 1  →  Nivel 2│
│ • Mesa de madera  ←activo│  [card]        [card]     [card]  │
│   Silla de madera        │                [card]     [card]  │
│   Estante modular        │                [card]             │
│   Cajón MDF              │                                   │
│   Armario roble          │                                   │
│ ─────────────────────    │                                   │
│ Filtros (solo tab MOs):  │                                   │
│ Estado: [Todos ▼]        │                                   │
└─────────────────────────────────────────────────────────────┘
```

### Tab 1 — Estructura BOM

- Columnas por nivel (0, 1, 2…) con `overflow-x: auto`
- Encabezado de columna: badge de color por nivel con etiqueta "Nivel N — descripción"
- Dentro de cada columna, los nodos se agrupan visualmente por padre: cada grupo tiene un separador con el nombre del producto padre, para distinguir de qué rama provienen cuando hay múltiples padres en el nivel anterior
- **BomProductCard** para productos manufacturados: borde sólido, referencia interna, cantidad, badge "tiene BOM →" si tiene sub-BOM propio
- **BomProductCard** para productos comprados: borde punteado, fondo gris, con un **checkmark (✓)** indicando "comprado / sin MO" — aparecen en ambas vistas para completar el árbol visual
- Máximo **5 niveles** visibles por defecto. Si el BOM tiene más niveles, se muestra un botón **"Ver más niveles (+N)"** al final del scroll horizontal que expande todos los subniveles restantes de una vez

### Tab 2 — MOs Activas

- Misma estructura de columnas por nivel, con agrupación por padre igual que Tab 1
- **MoBomCard** con: avatar + iniciales del responsable, referencia MO, producto, qty_producing/product_qty, badge de estado
- **BomProductCard** (comprados, con checkmark ✓) también aparece en esta vista para mantener el árbol completo y poder ver qué posición ocupa cada componente comprado en la cadena
- Badge de estado y color de header de card igual al `MoCard` del `mrp_dashboard` existente
- Columna vacía de MOs → texto "Sin MOs activas" en gris (los comprados con ✓ no cuentan como vacío)
- Auto-refresh cada 30 segundos (igual que `mrp_dashboard`)
- Indicador "↻ 30s" en el header cuando está actualizando
- Botón **"Ver más niveles (+N)"** aplica igualmente en esta vista

### Colores por nivel (ambos tabs)

| Nivel | Badge | Color cards |
|-------|-------|-------------|
| 0 | `bg-blue-100 text-blue-800` | `border-blue-300` / header `bg-blue-800` |
| 1 | `bg-sky-100 text-sky-800` | `border-sky-300` / header `bg-sky-600` |
| 2 | `bg-teal-100 text-teal-800` | `border-teal-300` / header `bg-teal-700` |
| 3+ | `bg-violet-100 text-violet-800` | escala violeta |

---

## 4. Componentes OWL

### `BomDashboard` (root)

**Estado reactivo:**
```js
{
  boms: [],              // lista para el sidebar [{id, name}]
  selectedBomId: false,  // BOM activo
  activeTab: 'structure',// 'structure' | 'mos'
  bomTree: null,         // árbol de BOM [{level, product, children, mos}]
  stateFilter: false,    // filtro de estado de MO (solo tab MOs)
  showAllLevels: false,  // false = máx 5 niveles, true = todos
  loading: false,
}
```

**Ciclo de vida:** `onMounted` → carga lista de BOMs → selecciona el primero automáticamente → inicia timer de 30s para refresh de MOs.

**Métodos:**
- `selectBom(id)` — actualiza `selectedBomId`, resetea `showAllLevels` a false, llama `loadData()`
- `setTab(tab)` — cambia `activeTab`
- `loadData()` — POST al controller con `bom_id` y `state_filter`
- `get levelColumns()` — transforma `bomTree` en array de columnas por nivel, agrupadas por padre dentro de cada columna. Si `showAllLevels` es false, corta en nivel 4 (índice 0–4 = 5 columnas máx)
- `get hiddenLevelsCount()` — cantidad de niveles ocultos (para el botón "Ver más +N")

### `BomSidebar`

Props: `boms`, `selectedBomId`, `onSelect`
Emite: click en BOM → llama `onSelect(id)`
Tiene buscador local (filtra `boms` por nombre sin llamar al servidor)

### `BomStructureView`

Props: `columns` (array de arrays de productos por nivel)
Renderiza columnas con `BomLevelColumn` + `BomProductCard`

### `BomMoView`

Props: `columns` (array de arrays de MOs por nivel), `loading`
Renderiza columnas con `BomLevelColumn` + `MoBomCard`

### `BomLevelColumn`

Props: `level` (número), `groups` (array de `{parentName, items}`), `emptyText`
- Renderiza cada grupo con un separador de texto con el nombre del padre cuando hay más de un grupo en la columna
- Maneja el encabezado coloreado por nivel y el estado vacío

### `BomProductCard`

Props: `product` — `{id, name, ref, qty, uom, has_bom, route_type}`
- `route_type: 'manufacture'` → card normal con borde sólido, badge "tiene BOM →" si `has_bom`
- `route_type: 'buy'` → card con borde punteado, fondo gris, checkmark **✓** en lugar de badge de estado. Aparece en ambos tabs.

### `MoBomCard`

Props: `mo` — mismos campos que `MoCard` del `mrp_dashboard`
Reutiliza los mismos colores de estado (`STATE_HEADER`, `STATE_BADGE`, `STATE_LABEL`)

---

## 5. Controller Python

**Ruta:** `POST /bom/dashboard/data`
**Auth:** `user`

**Request:**
```json
{ "bom_id": 1, "state_filter": false }
```

**Response:**
```json
{
  "boms": [{"id": 1, "name": "Mesa de madera"}, ...],
  "tree": [
    {
      "level": 0,
      "product_id": 10,
      "product_name": "Mesa de madera",
      "product_ref": "MESA-001",
      "qty": 1.0,
      "uom": "ud",
      "has_bom": true,
      "route_type": "manufacture",
      "mos": [
        {
          "id": 42,
          "name": "WH/MO/00042",
          "product_name": "Mesa de madera",
          "qty_producing": 1.0,
          "product_qty": 1.0,
          "state": "progress",
          "responsible_name": "German Rapp",
          "responsible_avatar": "/web/image/res.users/5/avatar_128",
          "lot": ""
        }
      ],
      "children": [
        {
          "level": 1,
          "product_id": 11,
          "product_name": "Tapa de madera",
          ...
          "children": [...]
        }
      ]
    }
  ]
}
```

**Lógica del controller:**

1. Carga `mrp.bom` con el `bom_id` dado
2. Expande recursivamente `bom_line_ids` hasta profundidad máxima de 5 niveles (previene loops)
3. Para cada producto encontrado en el árbol, busca MOs activas con `state not in ('done', 'cancel')`
4. Si `state_filter` viene en el request, agrega dominio adicional `[('state', '=', state_filter)]`
5. Detecta `route_type` mirando `product.route_ids` — si tiene ruta de manufactura = `'manufacture'`, si no = `'buy'`
6. `has_bom` = True si existe al menos un `mrp.bom` activo para ese producto

**Ruta adicional:** `POST /bom/dashboard/boms` — devuelve solo la lista de BOMs (para carga inicial rápida)

---

## 6. Vistas backend

### `bom_dashboard_menu.xml`

- Acción cliente (`ir.actions.client`) con tag `bom_dashboard.BomDashboard`
- Item de menú bajo Manufacturing: "Dashboard BOM"
- `groups="mrp.group_mrp_user"`

---

## 7. Integración con repo krasorx/odoo-dashboards

El directorio actual `odoo-tailwind-css/` se convierte en el repositorio `krasorx/odoo-dashboards` en GitHub. Contenido final del repo:

```
odoo-dashboards/
├── mrp_dashboard/    # addon existente (dashboard semanal por día)
├── bom_dashboard/    # addon nuevo (este spec)
├── custom_dashboards/# addon existente
└── docs/
```

---

## 8. No incluido en este scope

- Drag & drop de MOs entre niveles
- Notificaciones push / websocket
- Exportación del árbol a PDF/Excel
- Vista de componentes comprados con stock disponible
- Profundidad de BOM mayor a 5 niveles visible por defecto (el botón "Ver más" los expande todos)
- Filtro por equipo MRP en el bom_dashboard (está en mrp_dashboard)
