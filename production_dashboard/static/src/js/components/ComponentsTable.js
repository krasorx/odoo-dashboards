/** @odoo-module */
import { Component, useState, xml } from "@odoo/owl";

export class ComponentsTable extends Component {
    static props = { components: Array };
    static template = xml`
        <div class="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden mb-4">
            <table class="w-full text-sm">
                <thead class="bg-gray-50 text-gray-500 text-xs uppercase">
                    <tr>
                        <th class="text-left px-3 py-2 cursor-pointer" t-on-click="() => this.sortBy('name')">Componente</th>
                        <th class="text-right px-3 py-2 cursor-pointer" t-on-click="() => this.sortBy('qty_needed')">Cant.</th>
                        <th class="text-right px-3 py-2 cursor-pointer" t-on-click="() => this.sortBy('unit_cost')">Coste u.</th>
                        <th class="text-right px-3 py-2 cursor-pointer" t-on-click="() => this.sortBy('total_cost')">Coste tot.</th>
                        <th class="text-right px-3 py-2 cursor-pointer" t-on-click="() => this.sortBy('qty_available')">Stock</th>
                        <th class="text-right px-3 py-2 cursor-pointer" t-on-click="() => this.sortBy('lead_time')">Lead</th>
                        <th class="text-center px-3 py-2">Estado</th>
                    </tr>
                </thead>
                <tbody>
                    <t t-foreach="sorted" t-as="c" t-key="c.product_id">
                        <tr class="border-t border-gray-50 hover:bg-gray-50">
                            <td class="px-3 py-2 font-semibold text-gray-700"><t t-esc="c.name"/>
                                <span t-if="c.has_bom" class="ml-1 text-xs text-blue-400">(sub-BOM)</span></td>
                            <td class="px-3 py-2 text-right font-mono" t-esc="num(c.qty_needed)"/>
                            <td class="px-3 py-2 text-right font-mono" t-esc="num(c.unit_cost)"/>
                            <td class="px-3 py-2 text-right font-mono font-bold" t-esc="num(c.total_cost)"/>
                            <td class="px-3 py-2 text-right font-mono" t-esc="num(c.qty_available)"/>
                            <td class="px-3 py-2 text-right font-mono" t-esc="c.lead_time"/>
                            <td class="px-3 py-2 text-center">
                                <span t-if="c.has_stock" class="text-green-600 font-bold">✓</span>
                                <span t-else="" class="text-red-500 font-bold" t-esc="'falta ' + num(c.qty_missing)"/>
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
