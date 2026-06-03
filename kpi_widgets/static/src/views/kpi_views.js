/** @odoo-module */
import { registry } from "@web/core/registry";
import { listView } from "@web/views/list/list_view";
import { kanbanView } from "@web/views/kanban/kanban_view";
import { KpiBand } from "../kpi_band/kpi_band";
import { useKpis } from "../kpi_hook";

// Default model method called for KPI data. Override per action via
// context="{'kpi_method': 'my_method'}" (the view RNG schema forbids custom
// attributes on the <list>/<kanban> root, so config travels in the context).
const DEFAULT_KPI_METHOD = "get_view_kpis";

/**
 * Wraps a view's props fn so the KPI model method name is exposed as a
 * `kpiMethod` controller prop, read from the action context with a convention
 * fallback.
 */
function withKpiProps(baseView) {
    return (genericProps, descr, config) => {
        const props = baseView.props(genericProps, descr, config);
        props.kpiMethod = (genericProps.context && genericProps.context.kpi_method)
            || DEFAULT_KPI_METHOD;
        return props;
    };
}

/** Builds a KPI-enabled view object from any base list view object. */
export function makeKpiListView(baseView = listView) {
    class KpiListController extends baseView.Controller {
        static template = "kpi_widgets.KpiListController";
        static components = { ...baseView.Controller.components, KpiBand };
        setup() {
            super.setup();
            this.kpi = useKpis();
        }
    }
    return { ...baseView, Controller: KpiListController, props: withKpiProps(baseView) };
}

/** Builds a KPI-enabled view object from any base kanban view object. */
export function makeKpiKanbanView(baseView = kanbanView) {
    class KpiKanbanController extends baseView.Controller {
        static template = "kpi_widgets.KpiKanbanController";
        static components = { ...baseView.Controller.components, KpiBand };
        setup() {
            super.setup();
            this.kpi = useKpis();
        }
    }
    return { ...baseView, Controller: KpiKanbanController, props: withKpiProps(baseView) };
}

// Default js_classes for models whose base view has no custom js_class.
registry.category("views").add("kpi_list", makeKpiListView(listView));
registry.category("views").add("kpi_kanban", makeKpiKanbanView(kanbanView));
