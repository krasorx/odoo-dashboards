/** @odoo-module */
import { registry } from "@web/core/registry";
import { StockListView } from "@stock/views/stock_empty_list_help";
import { makeKpiListView } from "@kpi_widgets/views/kpi_views";

// Layer the KPI band on top of stock's list view so its custom Renderer
// (empty-list help) is preserved. vpicktree already uses js_class="stock_list_view";
// our inherited view swaps it to "kpi_stock_list".
registry.category("views").add("kpi_stock_list", makeKpiListView(StockListView));
