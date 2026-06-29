/** @odoo-module */
import { Component, useState, onWillStart, xml } from "@odoo/owl";
import { rpc } from "@web/core/network/rpc";
import { KpiCards } from "./KpiCards";
import { CostBreakdownChart } from "./CostBreakdownChart";
import { ComponentsTable } from "./ComponentsTable";
import { StockTraceabilityPanel } from "./StockTraceabilityPanel";
import { HistoryPanel } from "./HistoryPanel";
import { EstimationFilters } from "./EstimationFilters";
import { AiAnalysisPanel } from "./AiAnalysisPanel";

export class EstimationDashboard extends Component {
    static props = {
        action: { type: Object, optional: true },
        actionId: { type: Number, optional: true },
        updateActionState: { type: Function, optional: true },
        className: { type: String, optional: true },
    };
    static components = {
        KpiCards, CostBreakdownChart, ComponentsTable, StockTraceabilityPanel,
        HistoryPanel, EstimationFilters, AiAnalysisPanel,
    };
    static template = xml`
        <div class="pd-root" style="height:100vh; overflow:auto;">
            <div class="pd-shell">
                <header class="pd-masthead pd-rise">
                    <div>
                        <p class="pd-eyebrow">MRP · Planificación</p>
                        <h1 class="pd-title">Estimación de <em>Producción</em></h1>
                    </div>
                    <div class="pd-masthead-meta">
                        <t t-if="state.result">
                            <div t-esc="state.result.product.name"/>
                            <t t-if="state.cached">
                                <span class="pd-chip is-cache mt-1"><span class="pd-blip"/> desde caché</span>
                            </t>
                        </t>
                    </div>
                </header>

                <EstimationFilters state="state" products="state.products" bomVariants="state.bomVariants"
                    onCalc.bind="calculate" onProductChange.bind="loadVariants"/>

                <t t-if="state.result">
                    <div class="pd-sec"><span class="pd-idx">01</span><span>Indicadores</span><span class="pd-rule"/></div>
                    <KpiCards kpis="state.result.kpis" mode="state.result.mode"
                        extra="state.result.mode === 'cost' ? {max_qty: state.result.max_qty, remaining: state.result.remaining} : undefined"/>

                    <t t-if="state.result.alerts.length">
                        <div class="pd-alert pd-rise" style="margin:0 0 22px;">
                            <t t-foreach="state.result.alerts" t-as="a" t-key="a_index">
                                <div class="pd-alert-row">▲ <b t-esc="a.product"/>
                                    <t t-if="a.type === 'stock'"><span>— faltan <t t-esc="a.missing"/></span></t>
                                    <t t-else=""><span>— sin BOM</span></t>
                                </div>
                            </t>
                        </div>
                    </t>

                    <div class="pd-sec">
                        <span class="pd-idx">02</span><span>Componentes</span>
                        <div class="pd-export-actions">
                            <button type="button" class="pd-btn pd-btn-ghost pd-btn-sm"
                                t-att-disabled="state.exporting"
                                t-on-click="() => this.exportXlsx('flattened')">
                                <t t-if="state.exporting === 'flattened'">Exportando…</t>
                                <t t-else="">XLSX acumulado</t>
                            </button>
                            <button type="button" class="pd-btn pd-btn-ghost pd-btn-sm"
                                t-att-disabled="state.exporting"
                                t-on-click="() => this.exportXlsx('multilevel')">
                                <t t-if="state.exporting === 'multilevel'">Exportando…</t>
                                <t t-else="">XLSX multinivel</t>
                            </button>
                        </div>
                        <span class="pd-rule"/>
                    </div>
                    <div class="grid grid-cols-1 lg:grid-cols-3 gap-4">
                        <div class="lg:col-span-2">
                            <ComponentsTable components="state.result.components"/>
                            <StockTraceabilityPanel traceability="state.result.stock_traceability"/>
                        </div>
                        <div class="space-y-4">
                            <CostBreakdownChart breakdown="state.result.cost_breakdown"/>
                            <HistoryPanel history="state.history" onPick.bind="applyHistory"/>
                        </div>
                    </div>

                    <t t-if="state.aiAvailable">
                        <div class="pd-sec" style="margin-top:28px;"><span class="pd-idx">03</span><span>Asistente IA</span><span class="pd-rule"/></div>
                        <AiAnalysisPanel t-key="state.calcSeq" state="state" connectorName="state.aiConnector"/>
                    </t>
                </t>
                <t t-else="">
                    <div class="grid grid-cols-1 lg:grid-cols-3 gap-4">
                        <div class="lg:col-span-2">
                            <div class="pd-empty">
                                <div><div class="pd-empty-mark">⌖</div>Elegí un producto y calculá una estimación</div>
                            </div>
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
            aiAvailable: false, aiConnector: false, calcSeq: 0,
            exporting: false,
        });
        onWillStart(async () => {
            this.state.products = await rpc('/production/estimation/products', {});
            this.state.history = await rpc('/production/estimation/history', {});
            try {
                const ai = await rpc('/production/estimation/ai_status', {});
                this.state.aiAvailable = !!ai.available;
                this.state.aiConnector = ai.connector_name || false;
            } catch (e) {
                this.state.aiAvailable = false;
            }
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
            this.state.calcSeq++;  // remount the AI panel fresh for this estimation
            this.state.history = await rpc('/production/estimation/history', {});
        } catch (e) {
            console.error('[EstimationDashboard]', e);
        } finally {
            this.state.loading = false;
        }
    }
    async exportXlsx(exportType) {
        if (!this.state.product_id || this.state.exporting) return;
        this.state.exporting = exportType;
        try {
            const out = await rpc('/production/estimation/export_xlsx', {
                export_type: exportType,
                mode: this.state.mode,
                product_id: this.state.product_id,
                bom_id: this.state.bom_id || false,
                qty: this.state.qty,
                budget: this.state.budget,
                filters: this.filters,
            });
            const binary = atob(out.file);
            const bytes = new Uint8Array(binary.length);
            for (let i = 0; i < binary.length; i++) {
                bytes[i] = binary.charCodeAt(i);
            }
            const url = URL.createObjectURL(new Blob([bytes], { type: out.mimetype }));
            const link = document.createElement('a');
            link.href = url;
            link.download = out.filename;
            link.click();
            URL.revokeObjectURL(url);
        } catch (e) {
            console.error('[EstimationDashboard] export', e);
        } finally {
            this.state.exporting = false;
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
