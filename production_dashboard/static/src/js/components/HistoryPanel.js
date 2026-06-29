/** @odoo-module */
import { Component, useState, xml } from "@odoo/owl";

const DEFAULT_VISIBLE = 5;

export class HistoryPanel extends Component {
    static props = { history: Array, onPick: Function };
    static template = xml`
        <div class="pd-card pd-card--pad pd-rise">
            <div class="pd-sec" style="margin-bottom:8px;"><span>Últimas ejecuciones</span><span class="pd-rule"/></div>
            <t t-if="!props.history.length">
                <p style="font:500 12px/1.5 var(--mono); color:var(--faint); margin:6px 0 0;">Sin historial todavía.</p>
            </t>
            <div>
                <t t-foreach="visibleHistory" t-as="h" t-key="h.id">
                    <div class="pd-hist-row" t-on-click="() => props.onPick(h)">
                        <span class="pd-hist-name" t-esc="h.product"/>
                        <span class="pd-hist-meta" t-esc="h.mode === 'cost' ? ('$' + h.budget) : (h.qty + ' u')"/>
                        <span class="pd-hist-cost" t-esc="num(h.total_cost)"/>
                    </div>
                </t>
            </div>
            <t t-if="hiddenCount > 0">
                <button type="button" class="pd-hist-toggle" t-on-click="toggleExpanded">
                    <t t-if="state.expanded">Ver menos</t>
                    <t t-else="">Ver más (<t t-esc="hiddenCount"/>)</t>
                </button>
            </t>
        </div>
    `;
    setup() {
        this.state = useState({ expanded: false });
    }
    get visibleHistory() {
        const rows = this.props.history || [];
        if (this.state.expanded || rows.length <= DEFAULT_VISIBLE) {
            return rows;
        }
        return rows.slice(0, DEFAULT_VISIBLE);
    }
    get hiddenCount() {
        return Math.max(0, (this.props.history || []).length - DEFAULT_VISIBLE);
    }
    toggleExpanded() {
        this.state.expanded = !this.state.expanded;
    }
    num(v) { return (v || 0).toLocaleString(undefined, { maximumFractionDigits: 2 }); }
}