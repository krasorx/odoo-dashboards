/** @odoo-module */
import { registry } from "@web/core/registry";
import { listView } from "@web/views/list/list_view";
import { kanbanView } from "@web/views/kanban/kanban_view";
import { KpiBand } from "../kpi_band/kpi_band";
import { useKpis } from "../kpi_hook";

/**
 * Wraps a view's props fn so the root `kpi_method` arch attribute is exposed
 * as a `kpiMethod` controller prop. genericProps.arch is already an Element.
 */
function withKpiProps(baseView) {
    return (genericProps, descr, config) => {
        const props = baseView.props(genericProps, descr, config);
        props.kpiMethod = genericProps.arch.getAttribute("kpi_method") || false;
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
