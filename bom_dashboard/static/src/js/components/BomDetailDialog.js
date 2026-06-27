/** @odoo-module */
import { Component, useState, onWillStart, xml } from "@odoo/owl";
import { Dialog } from "@web/core/dialog/dialog";
import { rpc } from "@web/core/network/rpc";
import { useService } from "@web/core/utils/hooks";

export class BomDetailDialog extends Component {
    static components = { Dialog };
    static props = {
        bomId: Number,
        productId: Number,
        qty: { type: Number, optional: true },
        close: Function,
    };
    static template = xml`
        <Dialog title="'Detalle de BOM'" size="'lg'">
            <t t-if="state.loading">
                <div class="text-center text-gray-400 py-8">Cargando...</div>
            </t>
            <t t-else="">
                <div class="row mb-3">
                    <div class="col-6">
                        <div style="background:#eff6ff;border-radius:8px;padding:12px;">
                            <p style="font-size:11px;color:#60a5fa;font-weight:600;text-transform:uppercase;margin:0;">Coste estimado fabricación</p>
                            <p style="font-size:20px;font-weight:700;color:#1d4ed8;margin:0;" t-esc="fmt(state.data.kpis.total_cost)"/>
                        </div>
                    </div>
                    <div class="col-6">
                        <div style="background:#f9fafb;border-radius:8px;padding:12px;">
                            <p style="font-size:11px;color:#9ca3af;font-weight:600;text-transform:uppercase;margin:0;">Tiempo total (días)</p>
                            <p style="font-size:20px;font-weight:700;color:#374151;margin:0;" t-esc="state.data.kpis.total_lead_time"/>
                        </div>
                    </div>
                </div>
                <table class="table table-sm">
                    <thead>
                        <tr>
                            <th>Componente</th>
                            <th class="text-end">Cant.</th>
                            <th class="text-end">Coste u.</th>
                            <th class="text-end">Coste tot.</th>
                            <th class="text-end">Lead</th>
                        </tr>
                    </thead>
                    <tbody>
                        <t t-foreach="state.data.components" t-as="c" t-key="c.product_id">
                            <tr>
                                <td><t t-esc="c.name"/></td>
                                <td class="text-end" t-esc="num(c.qty_needed)"/>
                                <td class="text-end" t-esc="num(c.unit_cost)"/>
                                <td class="text-end fw-bold" t-esc="num(c.total_cost)"/>
                                <td class="text-end" t-esc="c.lead_time"/>
                            </tr>
                        </t>
                    </tbody>
                </table>
            </t>
            <t t-set-slot="footer">
                <button class="btn btn-primary" t-on-click="estimate">🚀 Estimar Producción</button>
                <button class="btn btn-secondary" t-on-click="() => this.props.close()">Cerrar</button>
            </t>
        </Dialog>
    `;
    setup() {
        this.action = useService("action");
        this.state = useState({ loading: true, data: { kpis: {}, components: [] } });
        onWillStart(async () => {
            const res = await rpc('/production/estimation/bom_detail',
                { bom_id: this.props.bomId, qty: this.props.qty || 1 });
            this.state.data = res && res.kpis ? res : { kpis: {}, components: [] };
            this.state.loading = false;
        });
    }
    fmt(v) { return (v || 0).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 }); }
    num(v) { return (v || 0).toLocaleString(undefined, { maximumFractionDigits: 2 }); }
    estimate() {
        this.props.close();
        this.action.doAction({
            type: 'ir.actions.client',
            tag: 'production_dashboard.EstimationDashboard',
            params: { product_id: this.props.productId, bom_id: this.props.bomId },
        });
    }
}
