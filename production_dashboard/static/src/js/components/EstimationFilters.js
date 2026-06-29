/** @odoo-module */
import { Component, xml } from "@odoo/owl";

export class EstimationFilters extends Component {
    static props = {
        state: Object, products: Array, bomVariants: Array,
        onCalc: Function, onProductChange: Function,
    };
    static template = xml`
        <div class="pd-card pd-card--pad mb-5 pd-rise">
            <div class="flex items-center justify-between gap-3 mb-4 flex-wrap">
                <div class="pd-seg">
                    <button t-att-class="segClass('quantity')" t-on-click="() => this.props.state.mode = 'quantity'">Por cantidad</button>
                    <button t-att-class="segClass('cost')" t-on-click="() => this.props.state.mode = 'cost'">Por coste</button>
                </div>
                <label class="pd-check">
                    <input type="checkbox" t-att-checked="props.state.only_in_stock"
                        t-on-change="ev => props.state.only_in_stock = ev.target.checked"/>
                    Solo con stock
                </label>
            </div>
            <div class="grid grid-cols-1 md:grid-cols-4 gap-3">
                <div>
                    <label class="pd-field-label">Producto</label>
                    <select class="pd-select" t-on-change="onProductSelect">
                        <option value="">— elegir —</option>
                        <t t-foreach="props.products" t-as="p" t-key="p.id">
                            <option t-att-value="p.id" t-att-selected="p.id === props.state.product_id" t-esc="p.name"/>
                        </t>
                    </select>
                </div>
                <div>
                    <label class="pd-field-label">Variante de BOM</label>
                    <select class="pd-select" t-on-change="onBomChange">
                        <t t-foreach="props.bomVariants" t-as="b" t-key="b.id">
                            <option t-att-value="b.id" t-att-selected="b.id === props.state.bom_id" t-esc="b.name"/>
                        </t>
                    </select>
                </div>
                <div t-if="props.state.mode === 'quantity'">
                    <label class="pd-field-label">Cantidad objetivo</label>
                    <input type="number" class="pd-input" t-att-value="props.state.qty" t-on-input="onQtyInput"/>
                </div>
                <div t-else="">
                    <label class="pd-field-label">Presupuesto objetivo</label>
                    <input type="number" class="pd-input" t-att-value="props.state.budget" t-on-input="onBudgetInput"/>
                </div>
                <div>
                    <label class="pd-field-label">Fecha de planificación</label>
                    <input type="date" class="pd-input" t-att-value="props.state.planning_date"
                        t-on-input="ev => props.state.planning_date = ev.target.value"/>
                </div>
            </div>
            <button class="pd-btn pd-btn-accent pd-btn-lg pd-btn-block mt-4"
                t-att-disabled="props.state.loading" t-on-click="() => props.onCalc()">
                <t t-if="props.state.loading"><span class="animate-pulse">↻ Calculando…</span></t>
                <t t-else="">Calcular estimación →</t>
            </button>
        </div>
    `;
    segClass(mode) {
        return 'pd-seg-btn' + (this.props.state.mode === mode ? ' is-on' : '');
    }
    onProductSelect(ev) {
        const id = parseInt(ev.target.value) || false;
        this.props.state.product_id = id;
        this.props.onProductChange(id);
    }
    onBomChange(ev) {
        this.props.state.bom_id = parseInt(ev.target.value) || false;
    }
    onQtyInput(ev) {
        this.props.state.qty = parseFloat(ev.target.value) || 0;
    }
    onBudgetInput(ev) {
        this.props.state.budget = parseFloat(ev.target.value) || 0;
    }
}
