/** @odoo-module */
import { Component, xml } from "@odoo/owl";

const STATE_HEADER = {
    draft:     'bg-gray-400',
    confirmed: 'bg-sky-500',
    progress:  'bg-orange-500',
    to_close:  'bg-blue-600',
    done:      'bg-green-600',
    waiting:   'bg-red-600',
};

const STATE_BADGE = {
    draft:     'bg-gray-100 text-gray-600',
    confirmed: 'bg-sky-100 text-sky-700',
    progress:  'bg-orange-100 text-orange-700',
    to_close:  'bg-blue-100 text-blue-700',
    done:      'bg-green-100 text-green-700',
    waiting:   'bg-red-100 text-red-700',
};

const STATE_LABEL = {
    draft:     'Borrador',
    confirmed: 'Confirmada',
    progress:  'En Progreso',
    to_close:  'Por Cerrar',
    done:      'Hecha',
    waiting:   'Esperando Op.',
};

export class MoCard extends Component {
    static template = xml`
        <div class="rounded-xl border border-gray-100 shadow-sm bg-white overflow-hidden mb-2 hover:shadow-md transition-shadow cursor-default">

            <!-- Header: foto + nombre responsable -->
            <div t-att-class="headerClass">
                <div class="w-10 h-10 rounded-full overflow-hidden bg-white/20 flex items-center justify-center flex-shrink-0 border-2 border-white/30">
                    <t t-if="props.mo.responsible_avatar">
                        <img
                            t-att-src="props.mo.responsible_avatar"
                            class="w-full h-full object-cover"
                            t-att-alt="props.mo.responsible_name"
                        />
                    </t>
                    <t t-else="">
                        <span class="text-white font-bold text-sm select-none" t-esc="initials"/>
                    </t>
                </div>
                <span class="text-white font-bold text-sm leading-tight ml-2 truncate flex-1" t-esc="props.mo.responsible_name or 'Sin asignar'"/>
            </div>

            <!-- Cuerpo -->
            <div class="px-3 py-2 space-y-1">
                <p class="text-xs font-mono text-gray-400 tracking-wide" t-esc="props.mo.name"/>

                <p class="text-sm font-semibold text-gray-800 leading-snug" t-esc="props.mo.product_name"/>

                <t t-foreach="props.mo.components.slice(0,2)" t-as="comp" t-key="comp_index">
                    <p class="text-xs text-gray-500 truncate">
                        <span class="mr-1 text-gray-300">-</span><t t-esc="comp"/>
                    </p>
                </t>

                <t t-if="props.mo.lot">
                    <p class="text-xs text-gray-400 flex items-center gap-1">
                        <span>&#127991;</span>
                        <span t-esc="props.mo.lot"/>
                    </p>
                </t>

                <div class="flex items-center justify-between pt-1 border-t border-gray-50 mt-1">
                    <span class="text-xs text-gray-500 font-mono">
                        <t t-esc="props.mo.qty_producing"/>/<t t-esc="props.mo.product_qty"/>
                    </span>
                    <span t-att-class="badgeClass" t-esc="stateLabel"/>
                </div>
            </div>
        </div>
    `;

    static props = { mo: Object };

    get headerClass() {
        const color = STATE_HEADER[this.props.mo.state] || 'bg-gray-400';
        return `flex items-center px-3 py-2.5 ${color}`;
    }

    get badgeClass() {
        const colors = STATE_BADGE[this.props.mo.state] || 'bg-gray-100 text-gray-600';
        return `inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium ${colors}`;
    }

    get stateLabel() {
        return STATE_LABEL[this.props.mo.state] || this.props.mo.state;
    }

    get initials() {
        return (this.props.mo.responsible_name || '?')
            .split(' ')
            .slice(0, 2)
            .map((w) => w[0] || '')
            .join('')
            .toUpperCase();
    }
}
