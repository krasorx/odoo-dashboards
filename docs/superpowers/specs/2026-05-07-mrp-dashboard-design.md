# MRP Dashboard — Design Spec
Date: 2026-05-07

## Resumen

Nuevo addon independiente `mrp_dashboard` para Odoo 18/19. Proporciona un dashboard semanal de órdenes de manufactura (MOs) estilo kanban, agrupadas por día de la semana, con navegación entre semanas, filtro por equipo MRP, y auto-refresh cada 30 segundos. Estilo moderno y minimalista con Tailwind CSS y OWL.

---

## 1. Módulo

**Nombre técnico:** `mrp_dashboard`  
**Versión:** `19.0.1.0.0`  
**Dependencias:** `mrp`, `hr`, `web`  
**Menú:** dentro del módulo Manufacturing (hereda `mrp.menu_mrp_root`)

---

## 2. Estructura de archivos

```
mrp_dashboard/
├── __manifest__.py
├── __init__.py
├── models/
│   ├── __init__.py
│   ├── mrp_team.py              # Nuevo modelo mrp.team
│   └── hr_employee.py           # Agrega mrp_team_ids a hr.employee
├── wizard/
│   ├── __init__.py
│   └── sync_employee_photo.py   # Wizard: copia foto empleado → usuario
├── controllers/
│   ├── __init__.py
│   └── mrp_dashboard_controller.py
├── security/
│   ├── mrp_dashboard_security.xml
│   └── ir.model.access.csv
├── views/
│   ├── mrp_team_views.xml
│   ├── hr_employee_views.xml
│   └── mrp_dashboard_menu.xml
└── static/src/
    ├── js/
    │   ├── mrp_dashboard_action.js
    │   └── components/
    │       ├── MrpDashboard.js
    │       ├── WeekColumn.js
    │       └── MoCard.js
    └── xml/
        └── mrp_dashboard_templates.xml
```

---

## 3. Modelos

### 3.1 `mrp.team` (nuevo)

| Campo | Tipo | Descripción |
|---|---|---|
| `name` | Char, required | Nombre del equipo |
| `member_ids` | Many2many → `hr.employee` | Miembros del equipo |
| `color` | Integer (0–11) | Color de header de cards en el dashboard |
| `active` | Boolean, default True | Archivado lógico |

**Seguridad:**
- Create/Write/Unlink: solo `base.group_system`
- Read: cualquier usuario con `mrp.group_mrp_user`

### 3.2 `hr.employee` (extensión)

| Campo | Tipo | Descripción |
|---|---|---|
| `mrp_team_ids` | Many2many → `mrp.team` | Equipos MRP a los que pertenece (inverso de `member_ids`) |

Un empleado puede pertenecer a múltiples equipos simultáneamente.

### 3.3 `mrp.production` — campos consumidos (sin modificar)

- `name` — referencia de la MO
- `product_id` — producto a fabricar
- `lot_producing_id` — lote asignado
- `qty_producing`, `product_qty` — cantidades
- `date_start` — fecha scheduled (columna del dashboard)
- `user_id` — responsable (relaciona con `hr.employee` via `user_id`)
- `state` — estado (`draft`, `confirmed`, `progress`, `to_close`, `done`)
- `move_raw_ids` — componentes (para mostrar en la card)

---

## 4. Wizard: Sincronización de foto

**Modelo:** `mrp.sync.employee.photo` (TransientModel)  
**Acción:** botón de servidor en `hr.employee`  
**Lógica:** si `employee.user_id` existe y `user_id.image_1920` está vacío, copia `employee.image_1920` al usuario.  
**Acceso:** solo `base.group_system`

---

## 5. Controlador JSON

**Ruta:** `POST /mrp/dashboard/weekly_orders`  
**Auth:** `user` (backend)  
**Request:**
```json
{ "week_start": "2026-05-04", "team_id": 1 }
```
**Response:**
```json
{
  "orders": {
    "2026-05-04": [
      {
        "id": 1,
        "name": "WH/MO/00001",
        "product_name": "Producto A",
        "lot": "LOT-000001",
        "qty_producing": 1.0,
        "product_qty": 1.0,
        "state": "to_close",
        "responsible_name": "German Rapp",
        "responsible_avatar": "<base64>",
        "components": ["Comp A [L1]", "Comp B [L2]"]
      }
    ],
    "2026-05-05": []
  },
  "teams": [
    { "id": 1, "name": "Team A" },
    { "id": 2, "name": "Team B" }
  ]
}
```

**Filtrado por team:** si `team_id` se pasa, filtra MOs donde `user_id.employee_id.mrp_team_ids` incluye ese team. Si `team_id = false`, muestra todas.

**Rango:** semana completa (lunes a domingo) de 7 días partiendo de `week_start`.

---

## 6. Componente OWL — `MrpDashboard`

### Estado reactivo (`useState`)
```js
{
  weekStart: Date,       // lunes de la semana actual
  selectedTeamId: false, // null = todos
  orders: {},            // { "YYYY-MM-DD": [mo, ...] }
  teams: [],             // lista de equipos disponibles
  loading: false,
  refreshTimer: null
}
```

### Ciclo de vida
- `onMounted`: llama `loadData()`, inicia `setInterval(loadData, 30_000)`, guarda ref del timer
- `onWillUnmount`: limpia el interval con `clearInterval`

### Métodos
- `loadData()`: POST a `/mrp/dashboard/weekly_orders` con `weekStart` y `selectedTeamId`
- `prevWeek()` / `nextWeek()`: ajusta `weekStart` ± 7 días, llama `loadData()`
- `onTeamChange(teamId)`: actualiza `selectedTeamId`, llama `loadData()`
- `get weekDays()`: devuelve array de 7 fechas (lunes a domingo)
- `get weekLabel()`: e.g. "May 04 – May 10, 2026"
- `isToday(date)`: boolean para resaltar columna actual

### Jerarquía de componentes
```
MrpDashboard
  ├── Header (inline en template)
  │     ├── Título + Team dropdown
  │     └── < semana anterior | label | semana siguiente >
  └── Grid 7 columnas
        └── WeekColumn(date, orders)
              └── MoCard × N  (o "Sin órdenes")
```

---

## 7. Componente `MoCard`

### Props
- `mo` — objeto con todos los campos de la MO

### Template (Tailwind)
```
rounded-xl border border-gray-100 shadow-sm bg-white overflow-hidden
  └── Header (bg dinámico por estado)
        ├── Avatar circular (img o iniciales)
        └── Nombre responsable (font-bold text-white)
  └── Body (px-3 py-2 space-y-1)
        ├── Referencia MO (text-xs font-mono text-gray-500)
        ├── Producto (text-sm font-semibold text-gray-800)
        ├── Componentes (text-xs text-gray-500, max 2 líneas)
        ├── Lote (text-xs text-gray-400)
        └── Qty y badge estado (flex justify-between)
```

### Colores de header por estado
| Estado | Clase Tailwind |
|---|---|
| `draft` | `bg-gray-400` |
| `confirmed` | `bg-sky-500` |
| `progress` | `bg-orange-500` |
| `to_close` | `bg-blue-600` |
| `done` | `bg-green-600` |
| `waiting` | `bg-red-600` |

---

## 8. Vistas backend

### `mrp_team_views.xml`
- Vista list + form de `mrp.team`
- Acción de menú solo visible para `base.group_system`
- Ubicación: Manufacturing > Configuración > Equipos MRP

### `hr_employee_views.xml`
- Hereda `hr.employee` form view
- Agrega pestaña "Equipos MRP" con widget many2many_tags de `mrp_team_ids`

### `mrp_dashboard_menu.xml`
- Acción cliente (`ir.actions.client`) que carga el tag `mrp_dashboard.MrpDashboard`
- Item de menú bajo Manufacturing: "Dashboard Semanal"

---

## 9. Seguridad

### `ir.model.access.csv`
```
id,name,model_id:id,group_id:id,perm_read,perm_write,perm_create,perm_unlink
access_mrp_team_user,mrp.team.user,mrp_dashboard.model_mrp_team,mrp.group_mrp_user,1,0,0,0
access_mrp_team_manager,mrp.team.manager,mrp_dashboard.model_mrp_team,base.group_system,1,1,1,1
access_mrp_sync_photo,mrp.sync.photo,mrp_dashboard.model_mrp_sync_employee_photo,base.group_system,1,1,1,1
```

---

## 10. Estilos Tailwind — guía visual

- **Grid semanal:** `grid grid-cols-7 gap-3` con `overflow-x-auto` para móvil
- **Columna de hoy:** `border-t-4 border-blue-500`, encabezado `text-blue-600 font-bold`
- **Columna normal:** `border-t-4 border-transparent`, encabezado `text-gray-500 font-medium`
- **Encabezado columna:** `text-xs uppercase tracking-wide`
- **Sin órdenes:** `text-gray-300 text-sm text-center py-10 select-none`
- **Dropdown de team:** `rounded-lg border border-gray-200 bg-white px-3 py-1.5 text-sm shadow-sm`
- **Botones navegación semana:** `rounded-lg border border-gray-200 p-1.5 hover:bg-gray-50`
- **Indicador refresh:** badge gris pulsante `animate-pulse` durante carga

---

## 11. No incluido en este scope

- Drag & drop de MOs entre días (cambio de `date_start`)
- Notificaciones push o websocket (el refresh es polling cada 30s)
- Exportación a PDF/Excel del dashboard
- Permisos por equipo (un usuario solo ve su equipo) — por ahora el dropdown filtra manualmente
