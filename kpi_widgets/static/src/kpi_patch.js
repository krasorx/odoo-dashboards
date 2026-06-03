/** @odoo-module */
import { patch } from "@web/core/utils/patch";
import { ListController } from "@web/views/list/list_controller";
import { KanbanController } from "@web/views/kanban/kanban_controller";
import { KpiBand } from "./kpi_band/kpi_band";
import { useKpis } from "./kpi_hook";

// Make KpiBand resolvable inside the inherited web.ListView / web.KanbanView
// templates for controllers that use the base components set.
ListController.components = { ...ListController.components, KpiBand };
KanbanController.components = { ...KanbanController.components, KpiBand };

patch(ListController.prototype, {
    setup() {
        super.setup();
        this.kpi = useKpis("list");
    },
});

patch(KanbanController.prototype, {
    setup() {
        super.setup();
        this.kpi = useKpis("kanban");
    },
});
