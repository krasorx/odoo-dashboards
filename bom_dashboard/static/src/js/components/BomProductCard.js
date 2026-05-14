/** @odoo-module */
import { Component, xml } from "@odoo/owl";

export class BomProductCard extends Component {
    static template = xml`
        <div t-att-class="cardClass">
            <!-- Header row -->
            <div class="flex items-center gap-2 px-3 py-2 border-b border-gray-100">
                <t t-if="isBought">
                    <span class="text-green-500 font-bold text-sm leading-none">✓</span>
                    <span class="text-xs font-semibold text-gray-400">Comprado</span>
                </t>
                <t t-else="">
                    <span class="text-xs font-semibold text-blue-600">fab.</span>
                    <t t-if="props.product.has_bom">
                        <span class="ml-auto text-xs font-bold text-blue-400 flex-shrink-0">tiene BOM →</span>
                    </t>
                </t>
            </div>
            <!-- Body -->
            <div class="px-3 py-2 space-y-1">
                <p class="text-xs font-bold text-gray-800 leading-snug" t-esc="props.product.product_name"/>
                <t t-if="props.product.product_ref">
                    <p class="text-xs font-mono text-gray-400 truncate" t-esc="props.product.product_ref"/>
                </t>
                <div class="flex items-center justify-between pt-1 mt-1 border-t border-gray-50">
                    <span class="text-xs text-gray-500 font-mono">
                        <t t-esc="props.product.qty"/>
                        <t t-esc="' ' + (props.product.uom or '')"/>
                    </span>
                </div>
            </div>
        </div>
    `;

    static props = { product: Object };

    get isBought() {
        return this.props.product.route_type === 'buy';
    }

    get cardClass() {
        return [
            'rounded-xl border overflow-hidden mb-2 bg-white transition-shadow cursor-default',
            this.isBought
                ? 'border-dashed border-gray-200 opacity-70'
                : 'border-gray-200 shadow-sm hover:shadow-md',
        ].join(' ');
    }
}
