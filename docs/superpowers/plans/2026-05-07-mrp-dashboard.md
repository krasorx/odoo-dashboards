# MRP Dashboard — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Crear el addon `mrp_dashboard` que muestra un dashboard semanal de órdenes de manufactura con navegación por semana, filtro por equipo MRP, y auto-refresh cada 30 segundos.

**Architecture:** Addon Odoo 18/19 independiente con modelo `mrp.team`, extensión de `hr.employee`, controlador JSON backend, y componentes OWL 2 con Tailwind CSS via CDN. El frontend lee `/mrp/dashboard/weekly_orders` y se refresca por polling cada 30 segundos.

**Tech Stack:** Python 3 (Odoo models + HTTP controller), OWL 2 (Odoo 18 component framework), Tailwind CSS CDN, XML (QWeb views + security)

---

## Mapa de archivos

| Archivo | Responsabilidad |
|---|---|
| `mrp_dashboard/__manifest__.py` | Declaración del módulo, dependencias, assets |
| `mrp_dashboard/__init__.py` | Importa models y controllers |
| `mrp_dashboard/models/mrp_team.py` | Modelo `mrp.team` |
| `mrp_dashboard/models/hr_employee.py` | Agrega `mrp_team_ids` a `hr.employee` |
| `mrp_dashboard/models/__init__.py` | Importa modelos |
| `mrp_dashboard/controllers/mrp_dashboard_controller.py` | Endpoint JSON `/mrp/dashboard/weekly_orders` |
| `mrp_dashboard/controllers/__init__.py` | Importa controlador |
| `mrp_dashboard/security/ir.model.access.csv` | ACLs para `mrp.team` |
| `mrp_dashboard/views/mrp_team_views.xml` | CRUD de equipos (solo admin) |
| `mrp_dashboard/views/hr_employee_views.xml` | Pestaña equipos + server action sync foto |
| `mrp_dashboard/views/mrp_dashboard_menu.xml` | Acción cliente OWL + ítem de menú |
| `mrp_dashboard/static/src/js/components/MoCard.js` | Card individual de una MO |
| `mrp_dashboard/static/src/js/components/WeekColumn.js` | Columna de un día |
| `mrp_dashboard/static/src/js/components/MrpDashboard.js` | Componente raíz del dashboard |
| `mrp_dashboard/static/src/js/mrp_dashboard_action.js` | Registra la acción cliente en el registry OWL |

---

### Task 1: Scaffold — estructura de directorios y archivos base

**Files:**
- Create: `mrp_dashboard/__manifest__.py`
- Create: `mrp_dashboard/__init__.py`
- Create: `mrp_dashboard/models/__init__.py`
- Create: `mrp_dashboard/controllers/__init__.py`

- [ ] **Step 1: Crear directorios del módulo**

```bash
cd /home/krasorx/proyectos-personales/odoo-tailwind-css
mkdir -p mrp_dashboard/{models,controllers,security,views,static/src/js/components}
touch mrp_dashboard/models/__init__.py
touch mrp_dashboard/controllers/__init__.py
```

- [ ] **Step 2: Crear `mrp_dashboard/__init__.py`**

Contenido completo del archivo:

```python
# -*- coding: utf-8 -*-
from . import models
from . import controllers
```

- [ ] **Step 3: Crear `mrp_dashboard/__manifest__.py`**

Contenido completo del archivo:

```python
# -*- coding: utf-8 -*-
{
    'name': 'MRP Dashboard',
    'version': '19.0.1.0.0',
    'category': 'Manufacturing',
    'summary': 'Weekly manufacturing orders dashboard with team filters and auto-refresh',
    'depends': ['mrp', 'hr', 'web'],
    'data': [
        'security/ir.model.access.csv',
        'views/mrp_team_views.xml',
        'views/hr_employee_views.xml',
        'views/mrp_dashboard_menu.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'mrp_dashboard/static/src/js/components/MoCard.js',
            'mrp_dashboard/static/src/js/components/WeekColumn.js',
            'mrp_dashboard/static/src/js/components/MrpDashboard.js',
            'mrp_dashboard/static/src/js/mrp_dashboard_action.js',
        ],
    },
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}
```

- [ ] **Step 4: Verificar estructura creada**

```bash
find mrp_dashboard -type f | sort
```

Salida esperada:
```
mrp_dashboard/__init__.py
mrp_dashboard/__manifest__.py
mrp_dashboard/controllers/__init__.py
mrp_dashboard/models/__init__.py
```

---

### Task 2: Modelos — `mrp.team` y extensión `hr.employee`

**Files:**
- Create: `mrp_dashboard/models/mrp_team.py`
- Create: `mrp_dashboard/models/hr_employee.py`
- Modify: `mrp_dashboard/models/__init__.py`

- [ ] **Step 1: Crear `mrp_dashboard/models/mrp_team.py`**

```python
# -*- coding: utf-8 -*-
from odoo import models, fields


class MrpTeam(models.Model):
    _name = 'mrp.team'
    _description = 'MRP Team'
    _order = 'name'

    name = fields.Char(string='Team Name', required=True)
    member_ids = fields.Many2many(
        'hr.employee',
        'mrp_team_employee_rel',
        'team_id',
        'employee_id',
        string='Members',
    )
    color = fields.Integer(string='Color Index', default=0)
    active = fields.Boolean(default=True)
```

- [ ] **Step 2: Crear `mrp_dashboard/models/hr_employee.py`**

```python
# -*- coding: utf-8 -*-
from odoo import models, fields


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    mrp_team_ids = fields.Many2many(
        'mrp.team',
        'mrp_team_employee_rel',
        'employee_id',
        'team_id',
        string='MRP Teams',
    )
```

- [ ] **Step 3: Actualizar `mrp_dashboard/models/__init__.py`**

```python
# -*- coding: utf-8 -*-
from . import mrp_team
from . import hr_employee
```

---

### Task 3: Seguridad — ACL del modelo `mrp.team`

**Files:**
- Create: `mrp_dashboard/security/ir.model.access.csv`

- [ ] **Step 1: Crear `mrp_dashboard/security/ir.model.access.csv`**

```csv
id,name,model_id:id,group_id:id,perm_read,perm_write,perm_create,perm_unlink
access_mrp_team_mrp_user,mrp.team mrp_user,mrp_dashboard.model_mrp_team,mrp.group_mrp_user,1,0,0,0
access_mrp_team_system,mrp.team system,mrp_dashboard.model_mrp_team,base.group_system,1,1,1,1
```

*Nota: si el Odoo de destino no tiene `mrp.group_mrp_user`, reemplazar por `mrp.group_mrp_manager`. Verificar en Ajustes > Técnico > Grupos.*

---

### Task 4: Controlador JSON — endpoint de órdenes semanales

**Files:**
- Create: `mrp_dashboard/controllers/mrp_dashboard_controller.py`
- Modify: `mrp_dashboard/controllers/__init__.py`

- [ ] **Step 1: Actualizar `mrp_dashboard/controllers/__init__.py`**

```python
# -*- coding: utf-8 -*-
from . import mrp_dashboard_controller
```

- [ ] **Step 2: Crear `mrp_dashboard/controllers/mrp_dashboard_controller.py`**

```python
# -*- coding: utf-8 -*-
from datetime import datetime, timedelta
from odoo import http
from odoo.http import request


class MrpDashboardController(http.Controller):

    @http.route('/mrp/dashboard/weekly_orders', type='json', auth='user')
    def weekly_orders(self, week_start, team_id=False):
        week_start_dt = datetime.strptime(week_start, '%Y-%m-%d')
        week_end_dt = week_start_dt + timedelta(days=7)

        domain = [
            ('date_start', '>=', week_start_dt.strftime('%Y-%m-%d 00:00:00')),
            ('date_start', '<', week_end_dt.strftime('%Y-%m-%d 00:00:00')),
        ]

        if team_id:
            team = request.env['mrp.team'].sudo().browse(int(team_id))
            user_ids = team.member_ids.mapped('user_id').ids
            if not user_ids:
                return {
                    'orders': self._empty_week(week_start_dt),
                    'teams': self._get_teams(),
                }
            domain.append(('user_id', 'in', user_ids))

        productions = request.env['mrp.production'].sudo().search(
            domain, order='date_start asc'
        )

        orders = self._empty_week(week_start_dt)
        for prod in productions:
            if not prod.date_start:
                continue
            day_key = prod.date_start.strftime('%Y-%m-%d')
            if day_key not in orders:
                continue

            user = prod.user_id
            avatar_url = (
                f'/web/image/res.users/{user.id}/avatar_128' if user else ''
            )

            components = []
            for move in prod.move_raw_ids[:3]:
                comp = move.product_id.display_name or ''
                lot = (
                    move.move_line_ids[:1].lot_id.name
                    if move.move_line_ids
                    else ''
                )
                if lot:
                    comp += f' [{lot}]'
                components.append(comp)

            orders[day_key].append({
                'id': prod.id,
                'name': prod.name,
                'product_name': prod.product_id.display_name or '',
                'lot': prod.lot_producing_id.name or '',
                'qty_producing': prod.qty_producing,
                'product_qty': prod.product_qty,
                'state': prod.state,
                'responsible_name': user.name if user else '',
                'responsible_avatar': avatar_url,
                'components': components,
            })

        return {'orders': orders, 'teams': self._get_teams()}

    def _empty_week(self, week_start_dt):
        return {
            (week_start_dt + timedelta(days=i)).strftime('%Y-%m-%d'): []
            for i in range(7)
        }

    def _get_teams(self):
        teams = request.env['mrp.team'].sudo().search([])
        return [{'id': t.id, 'name': t.name} for t in teams]
```

*Nota sobre campo de fecha: en Odoo 17+ el campo se llama `date_start`. Si el Odoo destino usa Odoo 16 o anterior, reemplazar `date_start` por `date_planned_start` en las dos referencias del dominio.*

---

### Task 5: Vistas backend — equipos, empleados, menú

**Files:**
- Create: `mrp_dashboard/views/mrp_team_views.xml`
- Create: `mrp_dashboard/views/hr_employee_views.xml`
- Create: `mrp_dashboard/views/mrp_dashboard_menu.xml`

- [ ] **Step 1: Crear `mrp_dashboard/views/mrp_team_views.xml`**

```xml
<?xml version="1.0" encoding="utf-8"?>
<odoo>
    <record id="mrp_team_view_list" model="ir.ui.view">
        <field name="name">mrp.team.list</field>
        <field name="model">mrp.team</field>
        <field name="arch" type="xml">
            <list string="MRP Teams">
                <field name="name"/>
                <field name="member_ids" widget="many2many_tags"/>
                <field name="active"/>
            </list>
        </field>
    </record>

    <record id="mrp_team_view_form" model="ir.ui.view">
        <field name="name">mrp.team.form</field>
        <field name="model">mrp.team</field>
        <field name="arch" type="xml">
            <form string="MRP Team">
                <sheet>
                    <div class="oe_title">
                        <label for="name"/>
                        <h1>
                            <field name="name" placeholder="Nombre del equipo"/>
                        </h1>
                    </div>
                    <group>
                        <field name="color"/>
                        <field name="active"/>
                    </group>
                    <notebook>
                        <page string="Miembros">
                            <field name="member_ids"
                                   widget="many2many_tags"
                                   domain="[('active', '=', True)]"/>
                        </page>
                    </notebook>
                </sheet>
            </form>
        </field>
    </record>

    <record id="action_mrp_team" model="ir.actions.act_window">
        <field name="name">MRP Teams</field>
        <field name="res_model">mrp.team</field>
        <field name="view_mode">list,form</field>
    </record>
</odoo>
```

- [ ] **Step 2: Crear `mrp_dashboard/views/hr_employee_views.xml`**

```xml
<?xml version="1.0" encoding="utf-8"?>
<odoo>
    <!-- Pestaña Equipos MRP en el formulario del empleado -->
    <record id="hr_employee_view_form_mrp_teams" model="ir.ui.view">
        <field name="name">hr.employee.form.mrp.teams</field>
        <field name="model">hr.employee</field>
        <field name="inherit_id" ref="hr.view_employee_form"/>
        <field name="arch" type="xml">
            <notebook position="inside">
                <page string="Equipos MRP" name="mrp_teams">
                    <group>
                        <field name="mrp_team_ids"
                               widget="many2many_tags"
                               string="Equipos MRP"/>
                    </group>
                </page>
            </notebook>
        </field>
    </record>

    <!-- Server action: copiar foto de empleado al usuario vinculado -->
    <record id="action_sync_employee_photo" model="ir.actions.server">
        <field name="name">Sincronizar Foto a Usuario</field>
        <field name="model_id" ref="hr.model_hr_employee"/>
        <field name="binding_model_id" ref="hr.model_hr_employee"/>
        <field name="binding_view_types">list,form</field>
        <field name="state">code</field>
        <field name="code">
for employee in records:
    if employee.user_id and not employee.user_id.image_1920:
        employee.user_id.sudo().write({'image_1920': employee.image_1920})
        </field>
        <field name="groups_id" eval="[(4, ref('base.group_system'))]"/>
    </record>
</odoo>
```

- [ ] **Step 3: Crear `mrp_dashboard/views/mrp_dashboard_menu.xml`**

```xml
<?xml version="1.0" encoding="utf-8"?>
<odoo>
    <!-- Acción cliente que monta el componente OWL MrpDashboard -->
    <record id="action_mrp_dashboard_client" model="ir.actions.client">
        <field name="name">Dashboard Semanal</field>
        <field name="tag">mrp_dashboard.MrpDashboard</field>
    </record>

    <!-- Ítem de menú bajo Manufacturing (secuencia 5 = primera posición) -->
    <menuitem
        id="menu_mrp_dashboard"
        name="Dashboard Semanal"
        parent="mrp.menu_mrp_root"
        action="action_mrp_dashboard_client"
        sequence="5"/>

    <!-- Ítem de configuración: Equipos MRP (solo system admin) -->
    <menuitem
        id="menu_mrp_teams"
        name="Equipos MRP"
        parent="mrp.menu_mrp_configuration"
        action="action_mrp_team"
        groups="base.group_system"
        sequence="100"/>
</odoo>
```

---

### Task 6: Componente OWL — `MoCard.js`

**Files:**
- Create: `mrp_dashboard/static/src/js/components/MoCard.js`

- [ ] **Step 1: Crear `mrp_dashboard/static/src/js/components/MoCard.js`**

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

export class MoCard extends Component {
    static template = xml`
        <div class="rounded-xl border border-gray-100 shadow-sm bg-white overflow-hidden mb-2 hover:shadow-md transition-shadow cursor-default">

            <!-- Header: foto + nombre responsable -->
            <div t-att-class="headerClass">
                <div class="w-10 h-10 rounded-full overflow-hidden bg-white/20 flex items-center justify-center flex-shrink-0 border-2 border-white/30">
                    <t t-if="props.mo.responsible_avatar">
                        <img
                            t-att-src="props.mo.responsible_avatar"
                            class="w-full h-full object-cover"
                            t-att-alt="props.mo.responsible_name"
                        />
                    </t>
                    <t t-else="">
                        <span class="text-white font-bold text-sm select-none" t-esc="initials"/>
                    </t>
                </div>
                <span class="text-white font-bold text-sm leading-tight ml-2 truncate flex-1" t-esc="props.mo.responsible_name or 'Sin asignar'"/>
            </div>

            <!-- Cuerpo -->
            <div class="px-3 py-2 space-y-1">
                <p class="text-xs font-mono text-gray-400 tracking-wide" t-esc="props.mo.name"/>

                <p class="text-sm font-semibold text-gray-800 leading-snug" t-esc="props.mo.product_name"/>

                <t t-foreach="props.mo.components.slice(0,2)" t-as="comp" t-key="comp_index">
                    <p class="text-xs text-gray-500 truncate">
                        <span class="mr-1 text-gray-300">-</span><t t-esc="comp"/>
                    </p>
                </t>

                <t t-if="props.mo.lot">
                    <p class="text-xs text-gray-400 flex items-center gap-1">
                        <span>&#127991;</span>
                        <span t-esc="props.mo.lot"/>
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
        return `flex items-center px-3 py-2.5 ${color}`;
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
            .split(' ')
            .slice(0, 2)
            .map((w) => w[0] || '')
            .join('')
            .toUpperCase();
    }
}
```

---

### Task 7: Componente OWL — `WeekColumn.js`

**Files:**
- Create: `mrp_dashboard/static/src/js/components/WeekColumn.js`

- [ ] **Step 1: Crear `mrp_dashboard/static/src/js/components/WeekColumn.js`**

```js
/** @odoo-module */
import { Component, xml } from "@odoo/owl";
import { MoCard } from "./MoCard";

export class WeekColumn extends Component {
    static template = xml`
        <div t-att-class="columnClass" class="flex flex-col min-w-0">
            <!-- Encabezado del día -->
            <div class="mb-3 pb-2 border-b border-gray-100 min-h-12">
                <p t-att-class="'text-xs uppercase tracking-wide font-semibold ' + (props.isToday ? 'text-blue-500' : 'text-gray-400')"
                   t-esc="dayName"/>
                <p t-att-class="'text-xl font-bold leading-none mt-0.5 ' + (props.isToday ? 'text-blue-600' : 'text-gray-700')"
                   t-esc="dayNumber"/>
            </div>

            <!-- Cards -->
            <div class="flex-1 space-y-0">
                <t t-if="props.orders.length">
                    <t t-foreach="props.orders" t-as="mo" t-key="mo.id">
                        <MoCard mo="mo"/>
                    </t>
                </t>
                <t t-else="">
                    <div class="text-gray-300 text-xs text-center py-10 select-none">
                        Sin órdenes
                    </div>
                </t>
            </div>
        </div>
    `;

    static components = { MoCard };

    static props = {
        date:    String,
        orders:  Array,
        isToday: Boolean,
    };

    get columnClass() {
        const todayBorder = this.props.isToday
            ? 'border-t-4 border-blue-500'
            : 'border-t-4 border-transparent';
        return `px-1 ${todayBorder}`;
    }

    get dayName() {
        const d = new Date(this.props.date + 'T12:00:00');
        return d.toLocaleDateString('es-AR', { weekday: 'long' }).toUpperCase();
    }

    get dayNumber() {
        const d = new Date(this.props.date + 'T12:00:00');
        return d.toLocaleDateString('es-AR', { month: 'short', day: 'numeric' }).toUpperCase();
    }
}
```

---

### Task 8: Componente OWL — `MrpDashboard.js`

**Files:**
- Create: `mrp_dashboard/static/src/js/components/MrpDashboard.js`

- [ ] **Step 1: Crear `mrp_dashboard/static/src/js/components/MrpDashboard.js`**

```js
/** @odoo-module */
import { Component, useState, onMounted, onWillUnmount, xml } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";
import { WeekColumn } from "./WeekColumn";

function getMondayOfCurrentWeek() {
    const today = new Date();
    const day = today.getDay();
    const diff = day === 0 ? -6 : 1 - day;
    const monday = new Date(today);
    monday.setDate(today.getDate() + diff);
    monday.setHours(0, 0, 0, 0);
    return monday;
}

function formatDate(date) {
    const y = date.getFullYear();
    const m = String(date.getMonth() + 1).padStart(2, '0');
    const d = String(date.getDate()).padStart(2, '0');
    return `${y}-${m}-${d}`;
}

export class MrpDashboard extends Component {
    static template = xml`
        <div class="min-h-screen bg-gray-50 font-sans">

            <!-- Header -->
            <div class="bg-white border-b border-gray-200 px-6 py-3 flex items-center justify-between shadow-sm sticky top-0 z-10">
                <div class="flex items-center gap-4">
                    <h1 class="text-lg font-bold text-gray-900 tracking-tight">MRP Dashboard</h1>

                    <select
                        class="rounded-lg border border-gray-200 bg-white px-3 py-1.5 text-sm shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-300 cursor-pointer"
                        t-on-change="onTeamChange"
                    >
                        <option value="">Todos los equipos</option>
                        <t t-foreach="state.teams" t-as="team" t-key="team.id">
                            <option
                                t-att-value="team.id"
                                t-att-selected="state.selectedTeamId === team.id"
                                t-esc="team.name"
                            />
                        </t>
                    </select>
                </div>

                <div class="flex items-center gap-2">
                    <t t-if="state.loading">
                        <span class="animate-pulse text-xs text-gray-400 mr-2">Actualizando...</span>
                    </t>
                    <button
                        class="rounded-lg border border-gray-200 w-8 h-8 flex items-center justify-center hover:bg-gray-50 transition-colors text-gray-500 text-lg"
                        t-on-click="prevWeek"
                    >&#8249;</button>
                    <span class="text-sm font-medium text-gray-700 w-44 text-center select-none" t-esc="weekLabel"/>
                    <button
                        class="rounded-lg border border-gray-200 w-8 h-8 flex items-center justify-center hover:bg-gray-50 transition-colors text-gray-500 text-lg"
                        t-on-click="nextWeek"
                    >&#8250;</button>
                </div>
            </div>

            <!-- Grid semanal -->
            <div class="overflow-x-auto">
                <div class="grid grid-cols-7 gap-3 p-4" style="min-width: 980px;">
                    <t t-foreach="weekDays" t-as="day" t-key="day">
                        <WeekColumn
                            date="day"
                            orders="state.orders[day] || []"
                            isToday="isToday(day)"
                        />
                    </t>
                </div>
            </div>
        </div>
    `;

    static components = { WeekColumn };

    setup() {
        this.rpc = useService("rpc");
        this.state = useState({
            weekStart:      getMondayOfCurrentWeek(),
            selectedTeamId: false,
            orders:         {},
            teams:          [],
            loading:        false,
        });
        this._refreshTimer = null;

        onMounted(() => {
            this._injectTailwind();
            this.loadData();
            this._refreshTimer = setInterval(() => this.loadData(), 30_000);
        });

        onWillUnmount(() => {
            if (this._refreshTimer) {
                clearInterval(this._refreshTimer);
            }
        });
    }

    _injectTailwind() {
        if (!document.querySelector('#mrp-tw-cdn')) {
            const script = document.createElement('script');
            script.id = 'mrp-tw-cdn';
            script.src = 'https://cdn.tailwindcss.com';
            document.head.appendChild(script);
        }
    }

    async loadData() {
        this.state.loading = true;
        try {
            const result = await this.rpc('/mrp/dashboard/weekly_orders', {
                week_start: formatDate(this.state.weekStart),
                team_id:    this.state.selectedTeamId || false,
            });
            this.state.orders = result.orders || {};
            this.state.teams  = result.teams  || [];
        } catch (err) {
            console.error('[MrpDashboard] Error cargando datos:', err);
        } finally {
            this.state.loading = false;
        }
    }

    get weekDays() {
        return Array.from({ length: 7 }, (_, i) => {
            const d = new Date(this.state.weekStart);
            d.setDate(d.getDate() + i);
            return formatDate(d);
        });
    }

    get weekLabel() {
        const start = this.state.weekStart;
        const end = new Date(start);
        end.setDate(end.getDate() + 6);
        const fmt = (d) =>
            d.toLocaleDateString('es-AR', { month: 'short', day: '2-digit' });
        return `${fmt(start)} – ${fmt(end)}, ${start.getFullYear()}`;
    }

    isToday(dateStr) {
        return dateStr === formatDate(new Date());
    }

    prevWeek() {
        const d = new Date(this.state.weekStart);
        d.setDate(d.getDate() - 7);
        this.state.weekStart = d;
        this.loadData();
    }

    nextWeek() {
        const d = new Date(this.state.weekStart);
        d.setDate(d.getDate() + 7);
        this.state.weekStart = d;
        this.loadData();
    }

    onTeamChange(ev) {
        const val = ev.target.value;
        this.state.selectedTeamId = val ? parseInt(val, 10) : false;
        this.loadData();
    }
}
```

---

### Task 9: Registrar la acción cliente OWL

**Files:**
- Create: `mrp_dashboard/static/src/js/mrp_dashboard_action.js`

- [ ] **Step 1: Crear `mrp_dashboard/static/src/js/mrp_dashboard_action.js`**

```js
/** @odoo-module */
import { registry } from "@web/core/registry";
import { MrpDashboard } from "./components/MrpDashboard";

registry.category("actions").add("mrp_dashboard.MrpDashboard", MrpDashboard);
```

---

### Task 10: Instalar y verificar

- [ ] **Step 1: Instalar el módulo en Odoo**

Opción A — línea de comandos (reemplazar `<db>` con el nombre real de la base de datos):
```bash
python odoo-bin -d <db> -u mrp_dashboard --stop-after-init
```

Opción B — desde la UI: Ajustes > Activar modo desarrollador > Apps > Actualizar lista > buscar "MRP Dashboard" > Instalar.

- [ ] **Step 2: Verificar que el modelo existe**

En modo debug, ir a: Ajustes > Técnico > Modelos, buscar `mrp.team`. Deben aparecer los campos `name`, `member_ids`, `color`, `active`.

- [ ] **Step 3: Verificar menú Manufacturing**

En el módulo Manufacturing debe aparecer "Dashboard Semanal" como primer ítem de menú.

- [ ] **Step 4: Probar el endpoint JSON**

Desde la consola del navegador (F12) en cualquier página de Odoo:
```js
fetch('/mrp/dashboard/weekly_orders', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
        jsonrpc: '2.0', method: 'call', id: 1,
        params: { week_start: '2026-05-05', team_id: false }
    })
}).then(r => r.json()).then(d => console.log(d.result));
```

Resultado esperado: objeto con clave `orders` (7 claves de fecha, cada una con array) y clave `teams` (array de equipos).

- [ ] **Step 5: Verificar el dashboard visual**

Abrir Manufacturing > Dashboard Semanal. Confirmar:
- El componente OWL carga sin errores en la consola
- Se ven 7 columnas (lunes a domingo)
- La columna de hoy tiene borde azul superior y texto azul
- Los estilos Tailwind aplican (fondo gris, cards blancas con sombra)
- Los cards muestran foto/iniciales del responsable, nombre grande en el header

- [ ] **Step 6: Verificar navegación de semana**

Hacer clic en `‹` y `›` para cambiar de semana. Las fechas en el encabezado deben actualizarse y los datos recargar.

- [ ] **Step 7: Verificar auto-refresh**

Abrir la pestaña Network (F12 > Network). Esperar 30 segundos. Debe aparecer una nueva llamada POST a `/mrp/dashboard/weekly_orders`.

- [ ] **Step 8: Verificar filtro por equipo**

Ir a Manufacturing > Configuración > Equipos MRP (visible solo con cuenta admin). Crear un equipo con al menos un empleado que sea responsable de alguna MO. Volver al dashboard, seleccionar el equipo en el dropdown — solo deben aparecer MOs de ese responsable.

- [ ] **Step 9: Verificar pestaña empleado**

Ir a RRHH > Empleados > abrir cualquier empleado. Debe aparecer la pestaña "Equipos MRP" con un campo de etiquetas para asignar equipos.

- [ ] **Step 10: Verificar acción sync foto**

En la lista de empleados (modo admin), seleccionar un empleado que tenga foto pero cuyo usuario vinculado no tenga foto. Ir a Acción > "Sincronizar Foto a Usuario". Confirmar que la foto del empleado se copia al usuario (verificable en Ajustes > Usuarios).
