/** @odoo-module */
import { Component, xml } from "@odoo/owl";

export class KpiCards extends Component {
    static props = { kpis: Object, mode: String, extra: { type: Object, optional: true } };
    static template = xml`
        <div class="grid grid-cols-2 md:grid-cols-4 gap-3 mb-6 pd-stagger">
            <div class="pd-kpi">
                <p class="pd-kpi-label">Coste unitario</p>
                <p class="pd-kpi-value" t-esc="fmt(props.kpis.unit_cost)"/>
            </div>
            <div class="pd-kpi is-accent">
                <p class="pd-kpi-label">Coste total</p>
                <p class="pd-kpi-value t-accent" t-esc="fmt(props.kpis.total_cost)"/>
            </div>
            <div class="pd-kpi">
                <p class="pd-kpi-label">Lead time</p>
                <p class="pd-kpi-value" t-esc="props.kpis.total_lead_time + ''"/>
                <p class="pd-kpi-sub">días</p>
            </div>
            <div t-att-class="'pd-kpi ' + stockTick">
                <p class="pd-kpi-label">En stock</p>
                <p class="pd-kpi-value" t-att-class="stockClass" t-esc="pct(props.kpis.pct_in_stock)"/>
                <p class="pd-kpi-sub" t-esc="props.kpis.missing_count + ' faltante(s) · ' + props.kpis.components_count + ' comp.'"/>
            </div>
            <t t-if="props.mode === 'cost' and props.extra">
                <div class="pd-kpi is-accent col-span-2">
                    <p class="pd-kpi-label">Cantidad máxima fabricable</p>
                    <p class="pd-kpi-value t-accent" t-esc="props.extra.max_qty + ''"/>
                </div>
                <div class="pd-kpi is-ok col-span-2">
                    <p class="pd-kpi-label">Presupuesto restante</p>
                    <p class="pd-kpi-value t-ok" t-esc="fmt(props.extra.remaining)"/>
                </div>
            </t>
        </div>
    `;
    fmt(v) { return (v || 0).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 }); }
    pct(v) { return (v || 0).toFixed(0) + '%'; }
    get stockClass() {
        const v = this.props.kpis.pct_in_stock || 0;
        return v >= 80 ? 't-ok' : (v >= 40 ? 't-warn' : 't-danger');
    }
    get stockTick() {
        const v = this.props.kpis.pct_in_stock || 0;
        return v >= 80 ? 'is-ok' : (v >= 40 ? 'is-warn' : 'is-danger');
    }
}
