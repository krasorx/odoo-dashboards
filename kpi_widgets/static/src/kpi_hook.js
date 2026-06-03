/** @odoo-module */
import { useState, useComponent, onWillStart } from "@odoo/owl";
import { useService, useBus } from "@web/core/utils/hooks";

/**
 * Adds KPI band state + behavior to a list/kanban controller.
 * Reads the model method name from this.props.kpiMethod (set by the view factory).
 * Returns { state, toggleFilter } for use in the controller template.
 */
export function useKpis() {
    const component = useComponent();
    const orm = useService("orm");
    const env = component.env;
    const resModel = component.props.resModel;
    const kpiMethod = component.props.kpiMethod;

    const state = useState({ kpis: [], loading: false, activeKpiId: false });

    async function load() {
        if (!kpiMethod) {
            return;
        }
        state.loading = true;
        try {
            const domain = env.searchModel.domain || [];
            state.kpis = await orm.call(resModel, kpiMethod, [domain]);
        } catch (e) {
            console.error("[kpi_widgets] Error loading KPIs:", e);
            state.kpis = [];
        } finally {
            state.loading = false;
        }
    }

    onWillStart(load);
    useBus(env.searchModel, "UPDATE", () => {
        // Refetch KPIs whenever the search domain/filters change.
        load();
    });

    async function toggleFilter(kpi) {
        if (!kpi.domain) {
            return;
        }
        const isActive = state.activeKpiId === kpi.id;
        state.activeKpiId = isActive ? false : kpi.id;
        const base = env.searchModel.domain || [];
        const extra = state.activeKpiId ? kpi.domain : [];
        await component.model.load({ domain: [...base, ...extra] });
    }

    return { state, toggleFilter };
}
