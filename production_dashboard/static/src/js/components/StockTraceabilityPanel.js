/** @odoo-module */
import { Component, useState, xml } from "@odoo/owl";

export class StockTraceabilityPanel extends Component {
    static props = { traceability: { type: Array, optional: true } };
    static template = xml`
        <div class="pd-card pd-card--pad pd-rise" style="margin-top:12px;">
            <div class="pd-sec" style="margin-bottom:8px;">
                <span class="pd-idx">2.5</span>
                <span>Trazabilidad · lotes / series</span>
                <span class="pd-rule"/>
            </div>
            <t t-if="!traceabilityRows.length">
                <p class="pd-muted-line">Sin stock interno con trazabilidad para los componentes visibles.</p>
            </t>
            <t t-else="">
                <t t-if="!state.expanded">
                    <button type="button" class="pd-hist-toggle" t-on-click="toggle">
                        Ver desglose (<t t-esc="traceabilityRows.length"/> producto(s))
                    </button>
                </t>
                <t t-else="">
                    <div class="pd-trace-wrap">
                        <t t-foreach="traceabilityRows" t-as="g" t-key="g.node_key">
                            <div class="pd-trace-group">
                                <div class="pd-trace-head">
                                    <span class="pd-trace-product" t-att-style="indent(g.depth)" t-esc="g.product"/>
                                    <span t-if="g.ref" class="pd-trace-ref" t-esc="g.ref"/>
                                    <span t-att-class="'pd-tag ' + trackingClass(g.tracking)" t-esc="trackingLabel(g.tracking)"/>
                                    <span class="pd-trace-meta">nec. <t t-esc="num(g.qty_needed)"/></span>
                                </div>
                                <table class="pd-table pd-table-compact">
                                    <thead>
                                        <tr>
                                            <th class="is-left">Lote / serie</th>
                                            <th class="is-left">Ubicación</th>
                                            <th>Cant.</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        <t t-foreach="g.lines" t-as="ln" t-key="ln_index">
                                            <tr>
                                                <td class="is-left pd-trace-lot" t-esc="lotLabel(ln)"/>
                                                <td class="is-left" t-esc="ln.location"/>
                                                <td class="pd-num" t-esc="num(ln.qty)"/>
                                            </tr>
                                        </t>
                                    </tbody>
                                </table>
                            </div>
                        </t>
                    </div>
                    <button type="button" class="pd-hist-toggle" t-on-click="toggle">Ocultar desglose</button>
                </t>
            </t>
        </div>
    `;
    setup() {
        this.state = useState({ expanded: false });
    }
    get traceabilityRows() {
        return this.props.traceability || [];
    }
    lotLabel(ln) {
        return ln.lot_name || '-';
    }
    toggle() {
        this.state.expanded = !this.state.expanded;
    }
    num(v) {
        return (v || 0).toLocaleString(undefined, { maximumFractionDigits: 2 });
    }
    indent(depth) {
        return `padding-left:${(depth || 0) * 14}px`;
    }
    trackingLabel(t) {
        if (t === 'serial') return 'serie';
        if (t === 'lot') return 'lote';
        return 'sin traza';
    }
    trackingClass(t) {
        if (t === 'serial') return 'pd-tag-mfg';
        if (t === 'lot') return 'pd-tag-buy';
        return 'pd-tag-ghost';
    }
}