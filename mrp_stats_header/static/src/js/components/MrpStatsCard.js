/** @odoo-module */
import { Component, xml } from "@odoo/owl";

// Matches STATE_BADGE and STATE_HEADER colors from mrp_dashboard/MoCard.js
const CARD_COLORS = {
    draft:     { border: 'border-gray-200',   text: 'text-gray-600',   activeBg: 'bg-gray-100' },
    confirmed: { border: 'border-sky-200',    text: 'text-sky-700',    activeBg: 'bg-sky-50'   },
    progress:  { border: 'border-orange-200', text: 'text-orange-700', activeBg: 'bg-orange-50' },
    to_close:  { border: 'border-blue-200',   text: 'text-blue-700',   activeBg: 'bg-blue-50'  },
    waiting:   { border: 'border-red-200',    text: 'text-red-700',    activeBg: 'bg-red-50'   },
    done:      { border: 'border-green-200',  text: 'text-green-700',  activeBg: 'bg-green-50' },
};

export class MrpStatsCard extends Component {
    static template = xml`
        <button
            t-att-class="cardClass"
            t-on-click="() => props.onClick(props.state)"
            type="button"
        >
            <span t-att-class="'text-2xl font-extrabold leading-none ' + colors.text"
                  t-esc="props.count"/>
            <span class="text-xs font-semibold uppercase tracking-wide text-gray-400 mt-0.5"
                  t-esc="props.label"/>
        </button>
    `;

    static props = {
        state: String,
        count: Number,
        label: String,
        active: Boolean,
        onClick: Function,
    };

    get colors() {
        return CARD_COLORS[this.props.state] || CARD_COLORS.draft;
    }

    get cardClass() {
        const c = this.colors;
        if (this.props.active) {
            return [
                'flex flex-col items-center justify-center px-4 py-3 rounded-xl',
                'border-2 transition-all duration-150 cursor-pointer select-none min-w-[90px]',
                c.activeBg, c.border, 'shadow-sm',
            ].join(' ');
        }
        return [
            'flex flex-col items-center justify-center px-4 py-3 rounded-xl',
            'border border-gray-100 bg-white transition-all duration-150',
            'cursor-pointer select-none min-w-[90px]',
            'hover:border-gray-200 hover:shadow-sm',
        ].join(' ');
    }
}
