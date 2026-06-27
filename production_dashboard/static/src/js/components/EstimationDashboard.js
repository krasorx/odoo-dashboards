/** @odoo-module */
import { Component, useState, onWillStart, xml } from "@odoo/owl";
import { rpc } from "@web/core/network/rpc";
import { KpiCards } from "./KpiCards";
import { CostBreakdownChart } from "./CostBreakdownChart";
import { ComponentsTable } from "./ComponentsTable";
import { HistoryPanel } from "./HistoryPanel";
import { EstimationFilters } from "./EstimationFilters";

export class EstimationDashboard extends Component {
    static props = {
        action: { type: Object, optional: true },
        actionId: { type: Number, optional: true },
        updateActionState: { type: Function, optional: true },
        className: { type: String, optional: true },
    };
    static components = { KpiCards, CostBreakdownChart, ComponentsTable, HistoryPanel, EstimationFilters };
    static template = xml`
        <div class="bg-gray-50 font-sans p-4 overflow-auto" style="height:100vh;">
            <div class="max-w-6xl mx-auto">
                <div class="flex items-center gap-3 mb-4">
                    <h1 class="text-xl font-bold text-gray-800">Estimación de Producción</h1>
                    <t t-if="state.cached">
                        <span class="text-xs bg-green-100 text-green-700 px-2 py-0.5 rounded-full font-bold">⚡ desde caché</span>
                    </t>
                </div>
                <EstimationFilters state="state" products="state.products" bomVariants="state.bomVariants"
                    onCalc.bind="calculate" onProductChange.bind="loadVariants"/>
                <t t-if="state.result">
                    <KpiCards kpis="state.result.kpis" mode="state.result.mode"
                        extra="state.result.mode === 'cost' ? {max_qty: state.result.max_qty, remaining: state.result.remaining} : undefined"/>
                    <t t-if="state.result.alerts.length">
                        <div class="bg-red-50 border border-red-200 rounded-xl p-3 mb-4 text-sm text-red-700">
                            <t t-foreach="state.result.alerts" t-as="a" t-key="a_index">
                                <div>⚠ <t t-esc="a.product"/> <t t-if="a.type === 'stock'">— faltan <t t-esc="a.missing"/></t><t t-else="">— sin BOM</t></div>
                            </t>
                        </div>
                    </t>
                    <div class="grid grid-cols-1 lg:grid-cols-3 gap-4">
                        <div class="lg:col-span-2">
                            <ComponentsTable components="state.result.components"/>
                        </div>
                        <div>
                            <CostBreakdownChart breakdown="state.result.cost_breakdown"/>
                            <HistoryPanel history="state.history" onPick.bind="applyHistory"/>
                        </div>
                    </div>
                </t>
                <t t-else="">
                    <div class="grid grid-cols-1 lg:grid-cols-3 gap-4">
                        <div class="lg:col-span-2 flex items-center justify-center text-gray-300 text-sm h-40">
                            Elegí un producto y calculá una estimación
                        </div>
                        <HistoryPanel history="state.history" onPick.bind="applyHistory"/>
                    </div>
                </t>
            </div>
        </div>
    `;
    setup() {
        this.state = useState({
            mode: 'quantity', product_id: false, bom_id: false,
            qty: 1, budget: 0, planning_date: false, only_in_stock: false,
            products: [], bomVariants: [], result: null, history: [],
            cached: false, loading: false,
        });
        onWillStart(async () => {
            this.state.products = await rpc('/production/estimation/products', {});
            this.state.history = await rpc('/production/estimation/history', {});
            const params = (this.props.action && this.props.action.params) || {};
            if (params.product_id) {
                this.state.product_id = params.product_id;
                await this.loadVariants(params.product_id);
                if (params.bom_id) this.state.bom_id = params.bom_id;
                await this.calculate();
            }
        });
    }
    get filters() {
        return { planning_date: this.state.planning_date || false, only_in_stock: this.state.only_in_stock };
    }
    async loadVariants(productId) {
        if (!productId) { this.state.bomVariants = []; this.state.bom_id = false; return; }
        const variants = await rpc('/production/estimation/bom_variants', { product_id: productId });
        this.state.bomVariants = variants;
        this.state.bom_id = variants.length ? variants[0].id : false;
    }
    async calculate() {
        if (!this.state.product_id) return;
        this.state.loading = true;
        try {
            const out = await rpc('/production/estimation/estimate', {
                mode: this.state.mode,
                product_id: this.state.product_id,
                bom_id: this.state.bom_id || false,
                qty: this.state.qty,
                budget: this.state.budget,
                filters: this.filters,
            });
            this.state.result = out.result;
            this.state.cached = out.cached;
            this.state.history = await rpc('/production/estimation/history', {});
        } catch (e) {
            console.error('[EstimationDashboard]', e);
        } finally {
            this.state.loading = false;
        }
    }
    async applyHistory(h) {
        this.state.mode = h.mode;
        this.state.product_id = h.product_id;
        await this.loadVariants(h.product_id);
        if (h.bom_id) this.state.bom_id = h.bom_id;
        if (h.mode === 'cost') this.state.budget = h.budget;
        else this.state.qty = h.qty;
        await this.calculate();
    }
}
