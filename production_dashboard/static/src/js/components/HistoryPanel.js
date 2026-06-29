/** @odoo-module */
import { Component, xml } from "@odoo/owl";

export class HistoryPanel extends Component {
    static props = { history: Array, onPick: Function };
    static template = xml`
        <div class="pd-card pd-card--pad pd-rise">
            <div class="pd-sec" style="margin-bottom:8px;"><span>Últimas ejecuciones</span><span class="pd-rule"/></div>
            <t t-if="!props.history.length">
                <p style="font:500 12px/1.5 var(--mono); color:var(--faint); margin:6px 0 0;">Sin historial todavía.</p>
            </t>
            <div>
                <t t-foreach="props.history" t-as="h" t-key="h.id">
                    <div class="pd-hist-row" t-on-click="() => props.onPick(h)">
                        <span class="pd-hist-name" t-esc="h.product"/>
                        <span class="pd-hist-meta" t-esc="h.mode === 'cost' ? ('$' + h.budget) : (h.qty + ' u')"/>
                        <span class="pd-hist-cost" t-esc="num(h.total_cost)"/>
                    </div>
                </t>
            </div>
        </div>
    `;
    num(v) { return (v || 0).toLocaleString(undefined, { maximumFractionDigits: 2 }); }
}
