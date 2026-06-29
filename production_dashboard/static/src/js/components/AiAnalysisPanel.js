/** @odoo-module */
import { Component, useState, xml } from "@odoo/owl";
import { rpc } from "@web/core/network/rpc";

/**
 * AI analysis of the current estimation. Rendered only when custom_agent is
 * installed (the parent gates it on /production/estimation/ai_status).
 *
 * It asks the backend for an action plan + natural-language summary, then lets
 * the user create the draft purchase orders / manufacturing orders needed to
 * fulfil the estimated production. Plan + record creation are deterministic
 * server-side; the LLM only writes the prose.
 *
 * NB: handlers are component methods (not inline expressions that call JS
 * globals) — OWL templates only expose a fixed set of globals, so e.g.
 * parseFloat() inside a t-on-* would blow up at runtime.
 */
export class AiAnalysisPanel extends Component {
    static props = {
        state: Object,
        connectorName: { type: [String, Boolean], optional: true },
    };
    static template = xml`
        <div class="pd-card pd-card--pad pd-ai pd-rise">
            <div class="pd-ai-head">
                <div class="flex items-center gap-3">
                    <span class="pd-ai-mark">✦</span>
                    <div>
                        <div style="font:700 14px/1 var(--sans); color:var(--ink);">Asistente de planificación</div>
                        <div t-if="props.connectorName" style="font:500 11px/1.4 var(--mono); color:var(--muted);" t-esc="props.connectorName"/>
                    </div>
                </div>
                <button t-on-click="() => this.analyze()" t-att-disabled="ui.loading" class="pd-btn pd-btn-accent">
                    <t t-if="ui.loading"><span class="animate-pulse">↻ Analizando…</span></t>
                    <t t-else=""><t t-esc="ui.analysis ? '↻ Re-analizar' : '✦ Analizar con IA'"/></t>
                </button>
            </div>

            <t t-if="ui.error">
                <div class="pd-alert" style="margin-top:14px;" t-esc="ui.error"/>
            </t>

            <t t-if="ui.analysis">
                <div class="pd-summary" style="margin-top:16px;" t-esc="ui.analysis.summary"/>
                <div t-if="!ui.analysis.ai_used" style="font:500 11px/1.4 var(--mono); color:var(--warn); margin-top:8px;">
                    resumen generado sin IA — configurá el token del agente para un análisis redactado
                </div>

                <div class="grid grid-cols-1 lg:grid-cols-2 gap-4" style="margin-top:18px;">
                    <!-- Purchases -->
                    <div class="pd-lane pd-lane-buy">
                        <div class="pd-lane-head">
                            <span t-esc="'Comprar · ' + ui.analysis.plan.purchase_count"/>
                            <span style="font-weight:600;" t-esc="'≈ ' + num(ui.analysis.plan.purchase_total)"/>
                        </div>
                        <t t-if="ui.analysis.plan.purchases.length">
                            <table class="pd-table">
                                <tbody>
                                    <t t-foreach="ui.analysis.plan.purchases" t-as="p" t-key="p.product_id">
                                        <tr>
                                            <td class="is-left pd-comp-name" t-esc="p.name"/>
                                            <td class="pd-num" t-esc="num(p.qty)"/>
                                            <td class="is-left" style="text-align:left; font:500 11px/1.3 var(--mono);">
                                                <span t-if="p.has_vendor" style="color:var(--muted);" t-esc="p.vendor_name"/>
                                                <span t-else="" style="color:var(--danger);">sin proveedor</span>
                                            </td>
                                        </tr>
                                    </t>
                                </tbody>
                            </table>
                            <div style="padding:10px;">
                                <button t-on-click="() => this.execute('purchase')" t-att-disabled="ui.executing" class="pd-btn pd-btn-accent pd-btn-block">
                                    <t t-if="ui.executing === 'purchase'"><span class="animate-pulse">↻ Generando…</span></t>
                                    <t t-else="">Generar órdenes de compra</t>
                                </button>
                            </div>
                        </t>
                        <t t-else="">
                            <div style="padding:14px; font:500 12px/1 var(--mono); color:var(--faint);">No faltan compras.</div>
                        </t>
                    </div>

                    <!-- Manufactures -->
                    <div class="pd-lane pd-lane-mfg">
                        <div class="pd-lane-head">
                            <span t-esc="'Fabricar · ' + ui.analysis.plan.manufacture_count"/>
                        </div>
                        <t t-if="ui.analysis.plan.manufactures.length">
                            <table class="pd-table">
                                <tbody>
                                    <t t-foreach="ui.analysis.plan.manufactures" t-as="m" t-key="m.product_id">
                                        <tr>
                                            <td class="is-left"><span class="pd-comp-name" t-esc="m.name"/>
                                                <span t-if="m.is_finished" class="pd-tag pd-tag-mfg">final</span></td>
                                            <td class="pd-num" t-esc="num(m.qty)"/>
                                        </tr>
                                    </t>
                                </tbody>
                            </table>
                            <div style="padding:10px;">
                                <button t-on-click="() => this.execute('manufacture')" t-att-disabled="ui.executing" class="pd-btn pd-btn-primary pd-btn-block">
                                    <t t-if="ui.executing === 'manufacture'"><span class="animate-pulse">↻ Generando…</span></t>
                                    <t t-else="">Generar órdenes de fabricación</t>
                                </button>
                            </div>
                        </t>
                        <t t-else="">
                            <div style="padding:14px; font:500 12px/1 var(--mono); color:var(--faint);">No hay nada para fabricar.</div>
                        </t>
                    </div>
                </div>

                <t t-if="ui.exec">
                    <div class="pd-exec" style="margin-top:16px;">
                        <div style="font:600 13px/1.4 var(--sans); color:var(--ok); margin-bottom:4px;" t-esc="ui.exec.message"/>
                        <t t-foreach="ui.exec.created" t-as="rec" t-key="rec.id">
                            <div style="padding:2px 0;">
                                <a t-att-href="rec.url" target="_blank" t-esc="rec.name || ('#' + rec.id)"/>
                                <span style="color:var(--muted); font-size:12px;" t-esc="' — ' + rec.label"/>
                            </div>
                        </t>
                    </div>
                </t>
            </t>

            <t t-if="!ui.analysis &amp;&amp; !ui.loading">
                <p style="font:500 12px/1.5 var(--mono); color:var(--faint); margin:14px 0 0;">Generá un resumen de las compras y fabricaciones necesarias para cumplir esta estimación, y creálas en un clic.</p>
            </t>
        </div>
    `;
    setup() {
        this.ui = useState({
            loading: false, analysis: null,
            executing: '', exec: null, error: '',
        });
    }
    get params() {
        const s = this.props.state;
        return {
            mode: s.mode,
            product_id: s.product_id,
            bom_id: s.bom_id || false,
            qty: s.qty,
            budget: s.budget,
            filters: { planning_date: s.planning_date || false, only_in_stock: s.only_in_stock },
        };
    }
    async analyze() {
        this.ui.loading = true;
        this.ui.error = '';
        this.ui.exec = null;
        try {
            this.ui.analysis = await rpc('/production/estimation/ai_analyze', this.params);
        } catch (e) {
            this.ui.error = 'No se pudo analizar la estimación.';
            console.error('[AiAnalysisPanel]', e);
        } finally {
            this.ui.loading = false;
        }
    }
    async execute(kind) {
        this.ui.executing = kind;
        this.ui.error = '';
        try {
            this.ui.exec = await rpc('/production/estimation/ai_execute', { kind, ...this.params });
        } catch (e) {
            this.ui.error = 'No se pudieron crear las órdenes.';
            console.error('[AiAnalysisPanel]', e);
        } finally {
            this.ui.executing = '';
        }
    }
    num(v) { return (v || 0).toLocaleString(undefined, { maximumFractionDigits: 2 }); }
}
