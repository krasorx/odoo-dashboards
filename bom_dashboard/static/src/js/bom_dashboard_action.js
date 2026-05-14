/** @odoo-module */
import { registry } from "@web/core/registry";
import { BomDashboard } from "./components/BomDashboard";

registry.category("actions").add("bom_dashboard.BomDashboard", BomDashboard);
