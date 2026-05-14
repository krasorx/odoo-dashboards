/** @odoo-module */
import { ListController } from "@web/views/list/list_controller";
import { useState, onMounted } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";
import { MrpStatsBanner } from "./components/MrpStatsBanner";

export class MrpProductionListController extends ListController {
    static template = "mrp_stats_header.MrpProductionListController";
    static components = { ...ListController.components, MrpStatsBanner };

    setup() {
        super.setup();
        this.rpc = useService("rpc");
        this.statsState = useState({
            scope: 'week',
            activeState: false,
            counts: { draft: 0, confirmed: 0, progress: 0, to_close: 0, waiting: 0, done: 0 },
        });
        onMounted(() => {
            this._injectTailwind();
            this.loadStats();
        });
    }

    _injectTailwind() {
        // dev-only CDN injection — remove before production
        if (!document.querySelector('#mrp-stats-tw-cdn')) {
            const s = document.createElement('script');
            s.id = 'mrp-stats-tw-cdn';
            s.src = 'https://cdn.tailwindcss.com';
            document.head.appendChild(s);
        }
    }

    async loadStats() {
        try {
            const counts = await this.rpc('/mrp/stats/counts', { scope: this.statsState.scope });
            this.statsState.counts = counts;
        } catch (e) {
            console.error('[MrpStatsHeader] Error loading stats:', e);
        }
    }

    setScope(scope) {
        this.statsState.scope = scope;
        this.loadStats();
    }

    async toggleStateFilter(state) {
        const isActive = this.statsState.activeState === state;
        this.statsState.activeState = isActive ? false : state;
        const base = this.props.domain || [];
        const extra = this.statsState.activeState
            ? [['state', '=', this.statsState.activeState]]
            : [];
        await this.model.load({ domain: [...base, ...extra] });
    }
}
