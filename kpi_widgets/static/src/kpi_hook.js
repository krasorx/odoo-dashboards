/** @odoo-module */
import { useState, useComponent, onWillStart } from "@odoo/owl";
import { useService, useBus } from "@web/core/utils/hooks";
import { session } from "@web/session";

/**
 * KPI band behavior for a list/kanban controller. Config-gated: does nothing
 * (no RPC) unless the model is in session.kpi_models. Returns { enabled, state,
 * toggleFilter }. Hooks are always registered (OWL rule); load() early-returns
 * when disabled.
 */
export function useKpis(viewType) {
    const component = useComponent();
    const orm = useService("orm");
    const env = component.env;
    const resModel = component.props.resModel;
    const enabled = Array.isArray(session.kpi_models)
        && session.kpi_models.includes(resModel);

    const state = useState({ kpis: [], loading: false, activeKpiId: false });

    async function load() {
        if (!enabled) {
            return;
        }
        state.loading = true;
        try {
            const domain = env.searchModel.domain || [];
            state.kpis = await orm.call(resModel, "get_view_kpis", [domain, viewType]);
        } catch (e) {
            console.error("[kpi_widgets] Error loading KPIs:", e);
            state.kpis = [];
        } finally {
            state.loading = false;
        }
    }

    onWillStart(load);
    useBus(env.searchModel, "UPDATE", () => load());

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

    return {
        get enabled() {
            return enabled;
        },
        state,
        toggleFilter,
    };
}
