/** @odoo-module */
import { Component, xml, useRef, onMounted, onWillUnmount, useEffect } from "@odoo/owl";

export class CostBreakdownChart extends Component {
    static props = { breakdown: Array };
    static template = xml`
        <div class="bg-white rounded-xl shadow-sm border border-gray-100 p-4 mb-4">
            <p class="text-xs text-gray-400 font-semibold uppercase mb-2">Desglose de costes</p>
            <div style="position:relative;height:260px;"><canvas t-ref="canvas"/></div>
        </div>
    `;
    setup() {
        this.canvas = useRef("canvas");
        this._chart = null;
        onMounted(() => this._render());
        useEffect(() => { this._render(); return () => {}; }, () => [this.props.breakdown]);
        onWillUnmount(() => { if (this._chart) this._chart.destroy(); });
    }
    _render(retries = 20) {
        const Chart = window.Chart;
        const el = this.canvas.el;
        if (!el) return;
        if (!Chart) {
            if (retries > 0) setTimeout(() => this._render(retries - 1), 150);
            return;
        }
        if (this._chart) this._chart.destroy();
        const data = this.props.breakdown || [];
        this._chart = new Chart(el, {
            type: 'doughnut',
            data: {
                labels: data.map(d => d.name),
                datasets: [{ data: data.map(d => d.value) }],
            },
            options: {
                responsive: true, maintainAspectRatio: false,
                plugins: { legend: { position: 'right' } },
            },
        });
    }
}
