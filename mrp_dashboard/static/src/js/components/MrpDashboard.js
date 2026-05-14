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
