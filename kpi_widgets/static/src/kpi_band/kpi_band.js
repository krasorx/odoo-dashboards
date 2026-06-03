/** @odoo-module */
import { Component, xml } from "@odoo/owl";
import { KpiCard } from "../kpi_card/kpi_card";

export class KpiBand extends Component {
    static template = xml`
        <div t-if="props.loading or props.kpis.length"
             class="o_kpi_band d-flex align-items-center flex-wrap gap-2 p-2 border-bottom bg-light">
            <t t-if="props.loading">
                <span class="o_kpi_loading text-muted d-flex align-items-center gap-2 p-2">
                    <i class="fa fa-spin fa-circle-o-notch"/> Cargando...
                </span>
            </t>
            <t t-else="">
                <t t-foreach="props.kpis" t-as="kpi" t-key="kpi.id">
                    <div t-att-class="dimClass(kpi)">
                        <KpiCard
                            id="kpi.id"
                            label="kpi.label"
                            value="kpi.value"
                            format="kpi.format"
                            icon="kpi.icon"
                            color="kpi.color"
                            active="props.activeKpiId === kpi.id"
                            onClick="kpi.domain ? props.onCardClick : undefined"
                        />
                    </div>
                </t>
            </t>
        </div>
    `;

    static components = { KpiCard };

    static props = {
        kpis: Array,
        loading: { type: Boolean, optional: true },
        activeKpiId: { type: [String, Number, Boolean], optional: true },
        onCardClick: { type: Function, optional: true },
    };

    dimClass(kpi) {
        const active = this.props.activeKpiId;
        return active && active !== kpi.id ? "opacity-50" : "";
    }
}
