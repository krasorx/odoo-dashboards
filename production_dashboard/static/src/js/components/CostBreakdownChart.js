/** @odoo-module */
import { Component, xml, useRef, onMounted, onWillUnmount, useEffect } from "@odoo/owl";

export class CostBreakdownChart extends Component {
    static props = { breakdown: Array };
    static template = xml`
        <div class="pd-card pd-card--pad pd-rise">
            <div class="pd-sec" style="margin-bottom:10px;"><span>Desglose de costes</span><span class="pd-rule"/></div>
            <div style="position:relative;height:250px;"><canvas t-ref="canvas"/></div>
        </div>
    `;
    // Industrial palette: safety orange → ochre → ink → slate, looping.
    static PALETTE = ['#e0531d', '#b0741b', '#7a5c3e', '#2d5e8c', '#2c7a4b',
                      '#9a4a2a', '#c9a227', '#534d44', '#8e887a', '#b53826'];
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
        const palette = this.constructor.PALETTE;
        const colors = data.map((d, i) => palette[i % palette.length]);
        this._chart = new Chart(el, {
            type: 'doughnut',
            data: {
                labels: data.map(d => d.name),
                datasets: [{
                    data: data.map(d => d.value),
                    backgroundColor: colors,
                    borderColor: '#faf8f3',
                    borderWidth: 2,
                    hoverOffset: 6,
                }],
            },
            options: {
                responsive: true, maintainAspectRatio: false,
                cutout: '62%',
                plugins: {
                    legend: {
                        position: 'right',
                        labels: {
                            boxWidth: 10, boxHeight: 10, usePointStyle: true, pointStyle: 'rectRounded',
                            color: '#534d44',
                            font: { family: "'IBM Plex Mono', monospace", size: 11 },
                        },
                    },
                },
            },
        });
    }
}
