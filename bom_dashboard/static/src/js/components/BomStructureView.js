/** @odoo-module */
import { Component, xml } from "@odoo/owl";
import { BomLevelColumn } from "./BomLevelColumn";

export class BomStructureView extends Component {
    static template = xml`
        <div class="overflow-x-auto h-full">
            <div class="flex gap-4 p-4 h-full items-start" style="min-width: max-content;">
                <t t-foreach="props.columns" t-as="col" t-key="col_index">
                    <BomLevelColumn
                        level="col_index"
                        groups="col"
                        mode="'structure'"
                        emptyText="'Sin productos'"
                    />
                    <!-- Arrow: show between columns and before "Ver más" -->
                    <t t-if="col_index !== props.columns.length - 1 or props.hiddenCount !== 0">
                        <div class="text-gray-300 text-xl self-start mt-7 flex-shrink-0">→</div>
                    </t>
                </t>

                <!-- Ver más button -->
                <t t-if="props.hiddenCount !== 0">
                    <div class="self-start mt-6 flex-shrink-0">
                        <button
                            class="text-xs font-semibold text-blue-500 border border-blue-200 rounded-full px-3 py-1.5 hover:bg-blue-50 transition-colors whitespace-nowrap"
                            t-on-click="() => this.props.onShowAll()"
                        >
                            Ver más niveles (+<t t-esc="props.hiddenCount"/>)
                        </button>
                    </div>
                </t>
            </div>
        </div>
    `;

    static components = { BomLevelColumn };

    static props = {
        columns: Array,
        hiddenCount: Number,
        onShowAll: Function,
    };
}
