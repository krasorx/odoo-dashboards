/** @odoo-module */
import { Component, xml } from "@odoo/owl";

export class EstimationFilters extends Component {
    static props = {
        state: Object, products: Array, bomVariants: Array,
        onCalc: Function, onProductChange: Function,
    };
    static template = xml`
        <div class="bg-white rounded-xl shadow-sm border border-gray-100 p-4 mb-4">
            <div class="flex gap-2 mb-4">
                <button t-att-class="btnClass('quantity')" t-on-click="() => this.props.state.mode = 'quantity'">📦 Por Cantidad</button>
                <button t-att-class="btnClass('cost')" t-on-click="() => this.props.state.mode = 'cost'">💲 Por Coste</button>
            </div>
            <div class="grid grid-cols-1 md:grid-cols-3 gap-3">
                <div>
                    <label class="text-xs text-gray-400 font-semibold">Producto</label>
                    <select class="w-full border rounded p-2 text-sm" t-on-change="onProductSelect">
                        <option value="">— elegir —</option>
                        <t t-foreach="props.products" t-as="p" t-key="p.id">
                            <option t-att-value="p.id" t-att-selected="p.id === props.state.product_id" t-esc="p.name"/>
                        </t>
                    </select>
                </div>
                <div>
                    <label class="text-xs text-gray-400 font-semibold">Variante de BOM</label>
                    <select class="w-full border rounded p-2 text-sm" t-on-change="ev => props.state.bom_id = parseInt(ev.target.value) || false">
                        <t t-foreach="props.bomVariants" t-as="b" t-key="b.id">
                            <option t-att-value="b.id" t-att-selected="b.id === props.state.bom_id" t-esc="b.name"/>
                        </t>
                    </select>
                </div>
                <div t-if="props.state.mode === 'quantity'">
                    <label class="text-xs text-gray-400 font-semibold">Cantidad objetivo</label>
                    <input type="number" class="w-full border rounded p-2 text-sm" t-att-value="props.state.qty"
                        t-on-input="ev => props.state.qty = parseFloat(ev.target.value) || 0"/>
                </div>
                <div t-else="">
                    <label class="text-xs text-gray-400 font-semibold">Presupuesto objetivo</label>
                    <input type="number" class="w-full border rounded p-2 text-sm" t-att-value="props.state.budget"
                        t-on-input="ev => props.state.budget = parseFloat(ev.target.value) || 0"/>
                </div>
                <div>
                    <label class="text-xs text-gray-400 font-semibold">Fecha de planificación</label>
                    <input type="date" class="w-full border rounded p-2 text-sm" t-att-value="props.state.planning_date"
                        t-on-input="ev => props.state.planning_date = ev.target.value"/>
                </div>
                <div class="flex items-end gap-2">
                    <label class="text-xs text-gray-500 flex items-center gap-1">
                        <input type="checkbox" t-att-checked="props.state.only_in_stock"
                            t-on-change="ev => props.state.only_in_stock = ev.target.checked"/>
                        Solo con stock
                    </label>
                </div>
            </div>
            <button class="mt-4 w-full bg-blue-600 hover:bg-blue-700 text-white font-bold py-3 rounded-xl text-base flex items-center justify-center gap-2"
                t-att-disabled="props.state.loading" t-on-click="() => props.onCalc()">
                <t t-if="props.state.loading"><span class="animate-pulse">↻ Calculando...</span></t>
                <t t-else="">⚡ Calcular Estimación</t>
            </button>
        </div>
    `;
    btnClass(mode) {
        const active = this.props.state.mode === mode;
        return ['flex-1 py-2 rounded-lg font-bold text-sm transition-colors',
            active ? 'bg-blue-600 text-white' : 'bg-gray-100 text-gray-500 hover:bg-gray-200'].join(' ');
    }
    onProductSelect(ev) {
        const id = parseInt(ev.target.value) || false;
        this.props.state.product_id = id;
        this.props.onProductChange(id);
    }
}
