/** @odoo-module */
import { ListController } from "@web/views/list/list_controller";
import { useState, onMounted } from "@odoo/owl";
import { rpc } from "@web/core/network/rpc";
import { MrpStatsBanner } from "./components/MrpStatsBanner";

export class MrpProductionListController extends ListController {
    static template = "mrp_stats_header.MrpProductionListController";
    static components = { ...ListController.components, MrpStatsBanner };

    setup() {
        super.setup();
        this.statsState = useState({
            scope: 'week',
            activeState: false,
            counts: { draft: 0, confirmed: 0, progress: 0, to_close: 0, waiting: 0, done: 0 },
        });
        onMounted(() => {
            this.loadStats();
        });
    }

    async loadStats() {
        try {
            const counts = await rpc('/mrp/stats/counts', { scope: this.statsState.scope });
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
