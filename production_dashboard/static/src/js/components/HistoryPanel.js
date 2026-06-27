/** @odoo-module */
import { Component, xml } from "@odoo/owl";

export class HistoryPanel extends Component {
    static props = { history: Array, onPick: Function };
    static template = xml`
        <div class="bg-white rounded-xl shadow-sm border border-gray-100 p-4">
            <p class="text-xs text-gray-400 font-semibold uppercase mb-2">Últimas ejecuciones</p>
            <t t-if="!props.history.length">
                <p class="text-xs text-gray-300">Sin historial todavía.</p>
            </t>
            <ul class="space-y-1">
                <t t-foreach="props.history" t-as="h" t-key="h.id">
                    <li class="flex items-center justify-between text-xs border-b border-gray-50 py-1 cursor-pointer hover:bg-gray-50 gap-2"
                        t-on-click="() => props.onPick(h)">
                        <span class="font-semibold text-gray-600 truncate" t-esc="h.product"/>
                        <span class="text-gray-400 flex-shrink-0" t-esc="h.mode === 'cost' ? ('$' + h.budget) : (h.qty + ' u')"/>
                        <span class="font-mono text-blue-500 flex-shrink-0" t-esc="num(h.total_cost)"/>
                    </li>
                </t>
            </ul>
        </div>
    `;
    num(v) { return (v || 0).toLocaleString(undefined, { maximumFractionDigits: 2 }); }
}
