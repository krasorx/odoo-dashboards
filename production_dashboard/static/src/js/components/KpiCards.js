/** @odoo-module */
import { Component, xml } from "@odoo/owl";

export class KpiCards extends Component {
    static props = { kpis: Object, mode: String, extra: { type: Object, optional: true } };
    static template = xml`
        <div class="grid grid-cols-2 md:grid-cols-4 gap-3 mb-4">
            <div class="bg-white rounded-xl shadow-sm border border-gray-100 p-4">
                <p class="text-xs text-gray-400 font-semibold uppercase">Coste unitario</p>
                <p class="text-2xl font-bold text-gray-800" t-esc="fmt(props.kpis.unit_cost)"/>
            </div>
            <div class="bg-white rounded-xl shadow-sm border border-gray-100 p-4">
                <p class="text-xs text-gray-400 font-semibold uppercase">Coste total</p>
                <p class="text-2xl font-bold text-blue-600" t-esc="fmt(props.kpis.total_cost)"/>
            </div>
            <div class="bg-white rounded-xl shadow-sm border border-gray-100 p-4">
                <p class="text-xs text-gray-400 font-semibold uppercase">Tiempo total (días)</p>
                <p class="text-2xl font-bold text-gray-800" t-esc="props.kpis.total_lead_time"/>
            </div>
            <div class="bg-white rounded-xl shadow-sm border border-gray-100 p-4">
                <p class="text-xs text-gray-400 font-semibold uppercase">% en stock</p>
                <p class="text-2xl font-bold" t-att-class="stockClass" t-esc="pct(props.kpis.pct_in_stock)"/>
            </div>
            <t t-if="props.mode === 'cost' and props.extra">
                <div class="bg-amber-50 rounded-xl shadow-sm border border-amber-200 p-4 col-span-2">
                    <p class="text-xs text-amber-500 font-semibold uppercase">Cantidad máxima fabricable</p>
                    <p class="text-2xl font-bold text-amber-700" t-esc="props.extra.max_qty"/>
                </div>
                <div class="bg-white rounded-xl shadow-sm border border-gray-100 p-4 col-span-2">
                    <p class="text-xs text-gray-400 font-semibold uppercase">Presupuesto restante</p>
                    <p class="text-2xl font-bold text-green-600" t-esc="fmt(props.extra.remaining)"/>
                </div>
            </t>
        </div>
    `;
    fmt(v) { return (v || 0).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 }); }
    pct(v) { return (v || 0).toFixed(0) + '%'; }
    get stockClass() {
        const v = this.props.kpis.pct_in_stock || 0;
        return v >= 80 ? 'text-green-600' : (v >= 40 ? 'text-amber-600' : 'text-red-600');
    }
}
