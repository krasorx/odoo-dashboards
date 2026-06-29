/** @odoo-module */
import { Component, useState, xml } from "@odoo/owl";

export class ComponentsTable extends Component {
    static props = { components: Array };
    static template = xml`
        <div class="pd-card overflow-hidden pd-rise">
            <div class="pd-comp-toolbar">
                <button type="button"
                    t-att-class="'pd-btn pd-btn-ghost pd-btn-sm ' + (state.multiLevel ? 'is-active' : '')"
                    t-on-click="toggleMultiLevel">
                    <t t-if="state.multiLevel">Ocultar análisis multinivel</t>
                    <t t-else="">Análisis multinivel</t>
                </button>
                <span t-if="state.multiLevel" class="pd-comp-hint">
                    Expandí cada componente fabricado para ver sub-BoMs
                </span>
            </div>
            <div t-att-class="'pd-comp-scroll' + (state.multiLevel ? ' is-multilevel' : '')">
            <table class="pd-table pd-table-components">
                <thead>
                    <tr>
                        <th class="is-left" t-on-click="() => this.sortBy('name')">Componente</th>
                        <th t-on-click="() => this.sortBy('qty_needed')">Cant.</th>
                        <th t-on-click="() => this.sortBy('unit_cost')">Coste u.</th>
                        <th t-on-click="() => this.sortBy('total_cost')">Coste tot.</th>
                        <th t-on-click="() => this.sortBy('real_cost')">Coste real</th>
                        <th t-on-click="() => this.sortBy('qty_available')">Stock</th>
                        <th t-on-click="() => this.sortBy('lead_time')">Lead</th>
                        <th class="is-left" style="text-align:left">Estado</th>
                    </tr>
                </thead>
                <tbody>
                    <t t-foreach="visibleRows" t-as="c" t-key="rowKey(c, c_index)">
                        <tr t-att-class="rowClass(c)">
                            <td class="is-left">
                                <div class="pd-comp-cell" t-att-style="indent(c.depth)">
                                    <t t-if="state.multiLevel and c.child_count">
                                        <button type="button" class="pd-tree-toggle"
                                            t-att-class="isExpanded(rowKey(c)) ? 'is-open' : ''"
                                            t-on-click="() => this.toggleNode(rowKey(c))">
                                            <t t-esc="treeToggleLabel(c)"/>
                                        </button>
                                    </t>
                                    <t t-else="">
                                        <span class="pd-tree-spacer"/>
                                    </t>
                                    <span class="pd-comp-name" t-esc="c.name"/>
                                    <span t-if="c.route === 'manufacture'" class="pd-tag pd-tag-mfg">fabr</span>
                                    <span t-else="" class="pd-tag pd-tag-buy">compra</span>
                                    <span t-if="c.tracking === 'serial'" class="pd-tag pd-tag-ser">serie</span>
                                    <span t-if="c.tracking === 'lot'" class="pd-tag pd-tag-lot">lote</span>
                                </div>
                            </td>
                            <td class="pd-num" t-esc="num(c.qty_needed)"/>
                            <td class="pd-num" t-esc="num(c.unit_cost)"/>
                            <td class="pd-num-strong" t-esc="num(c.total_cost)"/>
                            <td t-att-class="c.real_cost ? 'pd-num-strong' : 'pd-num'" t-esc="num(c.real_cost)"/>
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
        </div>
    `;
    setup() {
        this.state = useState({
            key: 'total_cost',
            asc: false,
            multiLevel: false,
            expanded: {},
        });
    }
    sortBy(key) {
        if (this.state.key === key) this.state.asc = !this.state.asc;
        else { this.state.key = key; this.state.asc = true; }
    }
    num(v) {
        return (v || 0).toLocaleString(undefined, { maximumFractionDigits: 2 });
    }
    rowKey(c, index = 0) {
        return c.node_key || `${c.product_id || 'row'}-${index}`;
    }
    treeToggleLabel(c) {
        return this.isExpanded(this.rowKey(c)) ? 'v' : '>';
    }
    indent(depth) {
        return `padding-left:${(depth || 0) * 16}px`;
    }
    rowClass(c) {
        return c.depth ? 'pd-row-child' : '';
    }
    isExpanded(nodeKey) {
        return !!this.state.expanded[nodeKey];
    }
    toggleNode(nodeKey) {
        this.state.expanded = {
            ...this.state.expanded,
            [nodeKey]: !this.state.expanded[nodeKey],
        };
    }
    toggleMultiLevel() {
        if (this.state.multiLevel) {
            this.state.multiLevel = false;
            this.state.expanded = {};
            return;
        }
        this.state.multiLevel = true;
        const expanded = {};
        const walk = (nodes) => {
            for (const n of nodes || []) {
                if (n.child_count) {
                    expanded[this.rowKey(n)] = true;
                }
                walk(n.children);
            }
        };
        walk(this.props.components);
        this.state.expanded = expanded;
    }
    flatten(nodes, depth = 0) {
        const out = [];
        const k = this.state.key;
        const asc = this.state.asc;
        const sorted = [...(nodes || [])].sort((a, b) => {
            const va = a[k], vb = b[k];
            if (typeof va === 'string') return asc ? va.localeCompare(vb) : vb.localeCompare(va);
            return asc ? va - vb : vb - va;
        });
        for (const node of sorted) {
            out.push(node);
            if (this.state.multiLevel && this.isExpanded(this.rowKey(node))) {
                out.push(...this.flatten(node.children, depth + 1));
            }
        }
        return out;
    }
    get visibleRows() {
        return this.flatten(this.props.components || []);
    }
}