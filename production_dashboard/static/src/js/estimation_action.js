/** @odoo-module */
import { registry } from "@web/core/registry";
import { EstimationDashboard } from "./components/EstimationDashboard";

registry.category("actions").add("production_dashboard.EstimationDashboard", EstimationDashboard);
