/**
 * Custom Dashboards - Odoo 18 with new OWL
 */

import { Component, useState, xml } from "@odoo/owl";

export class Dashboard extends Component {
    static template = xml`
        <div id="custom-dashboard">
            <!-- KPI Cards -->
            <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
                <div class="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
                    <div class="text-3xl mb-4">💵</div>
                    <div class="text-3xl font-bold text-gray-900" t-esc="invoiced_amount" t-options='{"format": "currency"}'>0.00</div>
                    <div class="text-sm text-gray-500 mt-2">Invoiced This Month</div>
                </div>

                <div class="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
                    <div class="text-3xl mb-4">📄</div>
                    <div class="text-3xl font-bold text-gray-900" t-esc="invoice_count">0</div>
                    <div class="text-sm text-gray-500 mt-2">Sales Invoices</div>
                </div>

                <div class="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
                    <div class="text-3xl mb-4">🏭</div>
                    <div class="text-3xl font-bold text-gray-900" t-esc="mps_completed_count">0</div>
                    <div class="text-sm text-gray-500 mt-2">Manufacturing Orders Done</div>
                </div>

                <div class="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
                    <div class="text-3xl mb-4">📦</div>
                    <div class="text-3xl font-bold text-gray-900" t-esc="mps_total_qty" t-options='{"format": "float"}'>0.00</div>
                    <div class="text-sm text-gray-500 mt-2">Total Qty Produced</div>
                </div>

                <div class="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
                    <div class="text-3xl mb-4">⏳</div>
                    <div class="text-3xl font-bold text-gray-900" t-esc="sales_pending_count">0</div>
                    <div class="text-sm text-gray-500 mt-2">Sales to Deliver</div>
                </div>

                <div class="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
                    <div class="text-3xl mb-4">📋</div>
                    <div class="text-3xl font-bold text-gray-900" t-esc="sales_pending_amount" t-options='{"format": "currency"}'>0.00</div>
                    <div class="text-sm text-gray-500 mt-2">Pending Sales Amount</div>
                </div>

                <div class="bg-red-50 rounded-lg shadow-sm border border-red-200 p-6">
                    <div class="text-3xl mb-4">⚠️</div>
                    <div class="text-3xl font-bold text-red-800" t-esc="overdue_count">0</div>
                    <div class="text-sm text-gray-500 mt-2">Overdue Invoices</div>
                </div>

                <div class="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
                    <div class="text-3xl mb-4">📈</div>
                    <div class="text-3xl font-bold text-gray-900" t-esc="totalRevenue" t-options='{"format": "currency"}'>0.00</div>
                    <div class="text-sm text-gray-500 mt-2">Total Revenue</div>
                </div>
            </div>

            <!-- Charts Section -->
            <div class="bg-white rounded-lg shadow-sm border border-gray-200 p-6 mb-8">
                <h2 class="text-lg font-semibold text-gray-900 mb-4 border-b pb-2">Monthly Sales Trend</h2>
                <canvas id="sales-chart" style="height: 300px;"></canvas>
            </div>

            <!-- Top Products -->
            <div class="bg-white rounded-lg shadow-sm border border-gray-200 p-6 mb-8">
                <h2 class="text-lg font-semibold text-gray-900 mb-4 border-b pb-2">Top Products by Sales</h2>
                <table class="w-full text-left border-collapse">
                    <thead>
                        <tr>
                            <th class="px-4 py-3 bg-gray-50 text-xs font-semibold text-gray-600 uppercase tracking-wider">Product</th>
                            <th class="px-4 py-3 bg-gray-50 text-xs font-semibold text-gray-600 uppercase tracking-wider">Qty Sold</th>
                            <th class="px-4 py-3 bg-gray-50 text-xs font-semibold text-gray-600 uppercase tracking-wider">Total Revenue</th>
                        </tr>
                    </thead>
                    <tbody>
                        <t t-foreach="top_products_data" t-as="product">
                            <tr>
                                <td class="px-4 py-3 text-sm text-gray-700 border-t border-gray-100" t-esc="product[0].name or 'Product'"></td>
                                <td class="px-4 py-3 text-sm text-gray-700 border-t border-gray-100" t-esc="product[1]">0</td>
                                <td class="px-4 py-3 text-sm text-gray-700 border-t border-gray-100" t-esc="(product[1] * product[2])" t-options='{"format": "float"}'>0.00</td>
                            </tr>
                        </t>
                    </tbody>
                </table>
            </div>

            <!-- Manufacturing Orders -->
            <div class="bg-white rounded-lg shadow-sm border border-gray-200 p-6 mb-8">
                <h2 class="text-lg font-semibold text-gray-900 mb-4 border-b pb-2">Recent Manufacturing Orders</h2>
                <table class="w-full text-left border-collapse">
                    <thead>
                        <tr>
                            <th class="px-4 py-3 bg-gray-50 text-xs font-semibold text-gray-600 uppercase tracking-wider">MO Number</th>
                            <th class="px-4 py-3 bg-gray-50 text-xs font-semibold text-gray-600 uppercase tracking-wider">Product</th>
                            <th class="px-4 py-3 bg-gray-50 text-xs font-semibold text-gray-600 uppercase tracking-wider">Qty</th>
                            <th class="px-4 py-3 bg-gray-50 text-xs font-semibold text-gray-600 uppercase tracking-wider">Status</th>
                            <th class="px-4 py-3 bg-gray-50 text-xs font-semibold text-gray-600 uppercase tracking-wider">Date</th>
                        </tr>
                    </thead>
                    <tbody>
                        <t t-if="mps_completed_count > 0" t-foreach="mps_completed_data" t-as="mo">
                            <tr>
                                <td class="px-4 py-3 text-sm text-gray-700 border-t border-gray-100">MO-2024-001</td>
                                <td class="px-4 py-3 text-sm text-gray-700 border-t border-gray-100" t-esc="mo[0].name or 'Product'"></td>
                                <td class="px-4 py-3 text-sm text-gray-700 border-t border-gray-100" t-esc="mo[1]">50</td>
                                <td class="px-4 py-3 text-sm text-gray-700 border-t border-gray-100"><span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">Completed</span></td>
                                <td class="px-4 py-3 text-sm text-gray-700 border-t border-gray-100">2024-01-15</td>
                            </tr>
                        </t>
                    </tbody>
                </table>
            </div>

            <!-- Overdue Invoices -->
            <div class="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
                <h2 class="text-lg font-semibold text-gray-900 mb-4 border-b pb-2">Overdue Invoices</h2>
                <table class="w-full text-left border-collapse">
                    <thead>
                        <tr>
                            <th class="px-4 py-3 bg-gray-50 text-xs font-semibold text-gray-600 uppercase tracking-wider">Invoice #</th>
                            <th class="px-4 py-3 bg-gray-50 text-xs font-semibold text-gray-600 uppercase tracking-wider">Customer</th>
                            <th class="px-4 py-3 bg-gray-50 text-xs font-semibold text-gray-600 uppercase tracking-wider">Amount</th>
                            <th class="px-4 py-3 bg-gray-50 text-xs font-semibold text-gray-600 uppercase tracking-wider">Due Date</th>
                            <th class="px-4 py-3 bg-gray-50 text-xs font-semibold text-gray-600 uppercase tracking-wider">Status</th>
                        </tr>
                    </thead>
                    <tbody>
                        <t t-if="overdue_count > 0" t-foreach="overdue_invoices_data" t-as="invoice">
                            <tr>
                                <td class="px-4 py-3 text-sm text-gray-700 border-t border-gray-100">INV/2024/001</td>
                                <td class="px-4 py-3 text-sm text-gray-700 border-t border-gray-100" t-esc="invoice[0].name or 'Customer'"></td>
                                <td class="px-4 py-3 text-sm text-gray-700 border-t border-gray-100" t-esc="invoice[2]" t-options='{"format": "currency"}'>0.00</td>
                                <td class="px-4 py-3 text-sm text-gray-700 border-t border-gray-100">2024-01-31</td>
                                <td class="px-4 py-3 text-sm text-gray-700 border-t border-gray-100"><span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-red-100 text-red-800">Overdue</span></td>
                            </tr>
                        </t>
                    </tbody>
                </table>
            </div>
        </div>
    `;

    setup() {
        this.state = useState({
            invoiced_amount: 0,
            invoice_count: 0,
            mps_completed_count: 0,
            mps_total_qty: 0,
            sales_pending_count: 0,
            sales_pending_amount: 0,
            overdue_count: 0,
            top_products_data: [],
            mps_completed_data: [],
            overdue_invoices_data: [],
            totalRevenue: 0,
        });

        this._rpc = this.rpc;
    }

    get invoiced_amount() {
        return this.state.invoiced_amount;
    }

    get invoice_count() {
        return this.state.invoice_count;
    }

    get mps_completed_count() {
        return this.state.mps_completed_count;
    }

    get mps_total_qty() {
        return this.state.mps_total_qty;
    }

    get sales_pending_count() {
        return this.state.sales_pending_count;
    }

    get sales_pending_amount() {
        return this.state.sales_pending_amount;
    }

    get overdue_count() {
        return this.state.overdue_count;
    }

    get top_products_data() {
        return this.state.top_products_data;
    }

    get mps_completed_data() {
        return this.state.mps_completed_data;
    }

    get overdue_invoices_data() {
        return this.state.overdue_invoices_data;
    }

    get totalRevenue() {
        return this.state.invoiced_amount + this.state.sales_pending_amount;
    }

    async loadData() {
        try {
            const today = new Date().toISOString().split('T')[0];
            const startOfMonth = new Date(new Date().setDate(1)).toISOString().split('T')[0];

            // Get invoiced this month
            const invoices = await this._rpc("/my/invoices/monthly", {
                date: startOfMonth,
            });

            this.state.invoiced_amount = invoices.invoiced_amount || 0;
            this.state.invoice_count = invoices.invoice_count || 0;

            // Get manufacturing orders completed
            const mps = await this._rpc("/my/mps/completed", {
                date: today,
            });

            this.state.mps_completed_count = mps.count || 0;
            this.state.mps_total_qty = mps.total_qty || 0;

            // Get sales pending
            const sales = await this._rpc("/my/sales/pending", {
                date: today,
            });

            this.state.sales_pending_count = sales.count || 0;
            this.state.sales_pending_amount = sales.amount || 0;

            // Get overdue invoices
            const overdue = await this._rpc("/my/overdue/invoices");

            this.state.overdue_count = overdue.count || 0;

            // Get top products
            const products = await this._rpc("/my/top/products", {
                date: startOfMonth,
                limit: 10,
            });

            this.state.top_products_data = products.data || [];

            // Get manufacturing orders data
            this.state.mps_completed_data = mps.data || [];

            // Get overdue invoices data
            this.state.overdue_invoices_data = overdue.data || [];

        } catch (error) {
            console.error("Error loading dashboard data:", error);
        }
    }
}
