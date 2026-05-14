/** @odoo-module */
import { Component, xml } from "@odoo/owl";
import { levelBadge } from "./bom_colors";
import { BomProductCard } from "./BomProductCard";
import { MoBomCard } from "./MoBomCard";

export class BomLevelColumn extends Component {
    static template = xml`
        <div class="flex flex-col flex-shrink-0 min-w-[180px] max-w-[210px]">
            <!-- Column header -->
            <div class="mb-3 flex-shrink-0">
                <span t-att-class="'text-xs font-bold uppercase tracking-wide px-2.5 py-1 rounded-full inline-block ' + badgeClass">
                    Nivel <t t-esc="props.level"/>
                </span>
            </div>

            <!-- Groups -->
            <div class="flex-1">
                <t t-foreach="props.groups" t-as="group" t-key="group_index">
                    <!-- Parent separator: only shown when multiple groups exist -->
                    <t t-if="props.groups.length > 1 and group.parentName">
                        <div class="text-xs text-gray-400 font-semibold uppercase tracking-wide mb-1 mt-3 px-1 truncate select-none">
                            ← <t t-esc="group.parentName"/>
                        </div>
                    </t>

                    <!-- Structure mode: render BomProductCard for every item -->
                    <t t-if="props.mode === 'structure'">
                        <t t-foreach="group.items" t-as="item" t-key="item.product_id">
                            <BomProductCard product="item"/>
                        </t>
                    </t>

                    <!-- MOs mode: render MoBomCard per MO + BomProductCard for bought items -->
                    <t t-else="">
                        <t t-foreach="group.items" t-as="item" t-key="item.product_id">
                            <t t-if="item.route_type === 'buy'">
                                <BomProductCard product="item"/>
                            </t>
                            <t t-else="">
                                <t t-if="item.mos and item.mos.length">
                                    <t t-foreach="item.mos" t-as="mo" t-key="mo.id">
                                        <MoBomCard mo="mo"/>
                                    </t>
                                </t>
                                <t t-else="">
                                    <div class="text-gray-300 text-xs text-center py-4 border border-dashed border-gray-100 rounded-xl mb-2 select-none"
                                         t-esc="item.product_name + ' — sin MOs'"/>
                                </t>
                            </t>
                        </t>
                    </t>
                </t>

                <!-- Empty column -->
                <t t-if="isEmpty">
                    <div class="text-gray-300 text-xs text-center py-10 select-none"
                         t-esc="props.emptyText or 'Sin elementos'"/>
                </t>
            </div>
        </div>
    `;

    static components = { BomProductCard, MoBomCard };

    static props = {
        level: Number,
        groups: Array,
        mode: String,
        emptyText: { type: String, optional: true },
    };

    get badgeClass() {
        return levelBadge(this.props.level);
    }

    get isEmpty() {
        return this.props.groups.every(g => !g.items || g.items.length === 0);
    }
}
