/** @odoo-module */
import { Component, xml } from "@odoo/owl";
import { MrpStatsCard } from "./MrpStatsCard";

const CARD_DEFS = [
    { state: 'draft',     label: 'Borrador'    },
    { state: 'confirmed', label: 'Confirmada'  },
    { state: 'progress',  label: 'En Progreso' },
    { state: 'to_close',  label: 'Por Cerrar'  },
    { state: 'waiting',   label: 'Esperando'   },
    { state: 'done',      label: 'Hecha'       },
];

export class MrpStatsBanner extends Component {
    static template = xml`
        <div class="flex items-center gap-3 px-4 py-2 bg-gray-50 border-b border-gray-200 overflow-x-auto flex-shrink-0">
            <div class="flex items-center gap-2 flex-1">
                <t t-foreach="cardDefs" t-as="def" t-key="def.state">
                    <div t-att-class="props.activeState and props.activeState !== def.state ? 'opacity-40 transition-opacity' : 'transition-opacity'">
                        <MrpStatsCard
                            state="def.state"
                            count="props.counts[def.state] || 0"
                            label="def.label"
                            active="props.activeState === def.state"
                            onClick="props.onCardClick"
                        />
                    </div>
                </t>
            </div>
            <div class="flex-shrink-0 flex bg-gray-200 rounded-full p-0.5 ml-2">
                <button t-att-class="scopeBtnClass('week')" t-on-click="() => props.onScopeChange('week')" type="button">
                    📅 Esta semana
                </button>
                <button t-att-class="scopeBtnClass('all')" t-on-click="() => props.onScopeChange('all')" type="button">
                    Todo
                </button>
            </div>
        </div>
    `;
    static components = { MrpStatsCard };
    static props = {
        counts: Object,
        activeState: { type: [String, Boolean] },
        scope: String,
        onCardClick: Function,
        onScopeChange: Function,
    };
    setup() { this.cardDefs = CARD_DEFS; }
    scopeBtnClass(scope) {
        const active = this.props.scope === scope;
        return ['rounded-full px-3 py-1 text-xs font-semibold transition-colors whitespace-nowrap',
            active ? 'bg-white text-blue-700 shadow-sm' : 'text-gray-500 hover:text-gray-700'].join(' ');
    }
}
