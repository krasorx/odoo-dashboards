/** @odoo-module */
import { registry } from "@web/core/registry";
import { listView } from "@web/views/list/list_view";
import { MrpProductionListController } from "./mrp_stats_list_controller";

registry.category("views").add("mrp_production_list", {
    ...listView,
    Controller: MrpProductionListController,
});
