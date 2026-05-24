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
        <div class="o_list_view_header d-flex align-items-center flex-wrap gap-2 p-2 border-bottom bg-light">
            <t t-foreach="cardDefs" t-as="def" t-key="def.state">
                <div t-att-class="props.activeState and props.activeState !== def.state ? 'opacity-50' : ''">
                    <MrpStatsCard
                        state="def.state"
                        count="props.counts[def.state] || 0"
                        label="def.label"
                        active="props.activeState === def.state"
                        onClick="props.onCardClick"
                    />
                </div>
            </t>
            <div class="btn-group btn-group-sm ms-auto" role="group">
                <button t-att-class="scopeBtnClass('week')" t-on-click="() => props.onScopeChange('week')" type="button" class="btn">
                    📅 Esta semana
                </button>
                <button t-att-class="scopeBtnClass('all')" t-on-click="() => props.onScopeChange('all')" type="button" class="btn">
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
        return active ? 'btn btn-primary active' : 'btn btn-outline-secondary';
    }
}
