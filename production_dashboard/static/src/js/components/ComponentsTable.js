/** @odoo-module */
import { Component, useState, xml } from "@odoo/owl";

export class ComponentsTable extends Component {
    static props = { components: Array };
    static template = xml`
        <div class="pd-card overflow-hidden pd-rise">
            <table class="pd-table">
                <thead>
                    <tr>
                        <th class="is-left" t-on-click="() => this.sortBy('name')">Componente</th>
                        <th t-on-click="() => this.sortBy('qty_needed')">Cant.</th>
                        <th t-on-click="() => this.sortBy('unit_cost')">Coste u.</th>
                        <th t-on-click="() => this.sortBy('total_cost')">Coste tot.</th>
                        <th t-on-click="() => this.sortBy('qty_available')">Stock</th>
                        <th t-on-click="() => this.sortBy('lead_time')">Lead</th>
                        <th class="is-left" style="text-align:left">Estado</th>
                    </tr>
                </thead>
                <tbody>
                    <t t-foreach="sorted" t-as="c" t-key="c.product_id">
                        <tr>
                            <td class="is-left"><span class="pd-comp-name" t-esc="c.name"/>
                                <span t-if="c.route === 'manufacture'" class="pd-tag pd-tag-mfg">fabr</span>
                                <span t-else="" class="pd-tag pd-tag-buy">compra</span></td>
                            <td class="pd-num" t-esc="num(c.qty_needed)"/>
                            <td class="pd-num" t-esc="num(c.unit_cost)"/>
                            <td class="pd-num-strong" t-esc="num(c.total_cost)"/>
                            <td class="pd-num" t-esc="num(c.qty_available)"/>
                            <td class="pd-num" t-esc="c.lead_time + ''"/>
                            <td class="is-left" style="text-align:left">
                                <span t-if="c.has_stock" class="pd-status ok"><span class="pd-dot"/> OK</span>
                                <span t-else="" class="pd-status miss"><span class="pd-dot"/><t t-esc="'faltan ' + num(c.qty_missing)"/></span>
                            </td>
                        </tr>
                    </t>
                </tbody>
            </table>
        </div>
    `;
    setup() { this.state = useState({ key: 'total_cost', asc: false }); }
    sortBy(key) {
        if (this.state.key === key) this.state.asc = !this.state.asc;
        else { this.state.key = key; this.state.asc = true; }
    }
    num(v) { return (v || 0).toLocaleString(undefined, { maximumFractionDigits: 2 }); }
    get sorted() {
        const arr = [...(this.props.components || [])];
        const k = this.state.key, asc = this.state.asc;
        arr.sort((a, b) => {
            const va = a[k], vb = b[k];
            if (typeof va === 'string') return asc ? va.localeCompare(vb) : vb.localeCompare(va);
            return asc ? va - vb : vb - va;
        });
        return arr;
    }
}
