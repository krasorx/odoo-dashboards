/** @odoo-module */
import { Component, xml } from "@odoo/owl";
import { MoCard } from "./MoCard";

export class WeekColumn extends Component {
    static template = xml`
        <div t-att-class="columnClass" class="flex flex-col min-w-0">
            <!-- Encabezado del día -->
            <div class="mb-3 pb-2 border-b border-gray-100 min-h-12">
                <p t-att-class="'text-xs uppercase tracking-wide font-semibold ' + (props.isToday ? 'text-blue-500' : 'text-gray-400')"
                   t-esc="dayName"/>
                <p t-att-class="'text-xl font-bold leading-none mt-0.5 ' + (props.isToday ? 'text-blue-600' : 'text-gray-700')"
                   t-esc="dayNumber"/>
            </div>

            <!-- Cards -->
            <div class="flex-1 space-y-0">
                <t t-if="props.orders.length">
                    <t t-foreach="props.orders" t-as="mo" t-key="mo.id">
                        <MoCard mo="mo"/>
                    </t>
                </t>
                <t t-else="">
                    <div class="text-gray-300 text-xs text-center py-10 select-none">
                        Sin órdenes
                    </div>
                </t>
            </div>
        </div>
    `;

    static components = { MoCard };

    static props = {
        date:    String,
        orders:  Array,
        isToday: Boolean,
    };

    get columnClass() {
        const todayBorder = this.props.isToday
            ? 'border-t-4 border-blue-500'
            : 'border-t-4 border-transparent';
        return `px-1 ${todayBorder}`;
    }

    get dayName() {
        const d = new Date(this.props.date + 'T12:00:00');
        return d.toLocaleDateString('es-AR', { weekday: 'long' }).toUpperCase();
    }

    get dayNumber() {
        const d = new Date(this.props.date + 'T12:00:00');
        return d.toLocaleDateString('es-AR', { month: 'short', day: 'numeric' }).toUpperCase();
    }
}
