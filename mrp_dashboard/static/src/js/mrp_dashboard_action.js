/** @odoo-module */
import { registry } from "@web/core/registry";
import { MrpDashboard } from "./components/MrpDashboard";

registry.category("actions").add("mrp_dashboard.MrpDashboard", MrpDashboard);
