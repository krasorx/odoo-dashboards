/** @odoo-module */
import { Component, useState, xml } from "@odoo/owl";

const STATE_OPTIONS = [
    { value: '',          label: 'Todos los estados' },
    { value: 'draft',     label: 'Borrador' },
    { value: 'confirmed', label: 'Confirmada' },
    { value: 'progress',  label: 'En Progreso' },
    { value: 'to_close',  label: 'Por Cerrar' },
    { value: 'waiting',   label: 'Esperando Op.' },
];

export class BomSidebar extends Component {
    static template = xml`
        <div class="bg-gray-900 flex-shrink-0 flex flex-col" style="width:200px;">
            <!-- Brand header -->
            <div class="px-3 py-3.5 border-b border-gray-700 flex-shrink-0">
                <span class="text-xs font-bold text-gray-100 tracking-wide">BOM Dashboard</span>
            </div>

            <!-- Search -->
            <div class="px-2.5 py-2 flex-shrink-0">
                <div class="bg-gray-700 rounded-md px-2.5 py-1.5 flex items-center gap-1.5">
                    <span class="text-gray-400 text-xs select-none">🔍</span>
                    <input
                        class="bg-transparent text-xs text-gray-200 placeholder-gray-500 outline-none w-full"
                        placeholder="Buscar BOM..."
                        t-on-input="onSearch"
                    />
                </div>
            </div>

            <!-- BOM list -->
            <div class="flex-1 overflow-y-auto px-2 py-1 min-h-0">
                <div class="text-gray-500 text-xs font-bold uppercase px-1.5 py-1 mb-1 tracking-wide">
                    Bills of Materials
                </div>
                <t t-foreach="filteredBoms" t-as="bom" t-key="bom.id">
                    <button
                        t-att-class="bomItemClass(bom.id)"
                        t-on-click="() => this.props.onSelect(bom.id)"
                    >
                        <span t-att-class="'w-1.5 h-1.5 rounded-full flex-shrink-0 ' + (props.selectedBomId === bom.id ? 'bg-blue-400' : 'bg-gray-600')"/>
                        <span class="truncate" t-esc="bom.name"/>
                    </button>
                </t>
                <t t-if="!filteredBoms.length">
                    <div class="text-gray-600 text-xs text-center py-6 select-none">Sin resultados</div>
                </t>
            </div>

            <!-- State filter — only visible in MOs tab -->
            <t t-if="props.activeTab === 'mos'">
                <div class="px-2.5 py-3 border-t border-gray-700 flex-shrink-0">
                    <div class="text-gray-500 text-xs font-bold uppercase mb-2 tracking-wide">Filtros</div>
                    <select
                        class="w-full bg-gray-700 border border-gray-600 rounded-md px-2 py-1.5 text-xs text-gray-300 outline-none focus:ring-1 focus:ring-blue-500 cursor-pointer"
                        t-on-change="onStateChange"
                    >
                        <t t-foreach="stateOptions" t-as="opt" t-key="opt.value">
                            <option
                                t-att-value="opt.value"
                                t-att-selected="props.stateFilter === opt.value"
                                t-esc="opt.label"
                            />
                        </t>
                    </select>
                </div>
            </t>
        </div>
    `;

    static props = {
        boms: Array,
        selectedBomId: { type: [Number, Boolean] },
        onSelect: Function,
        stateFilter: { type: [String, Boolean] },
        onStateFilter: Function,
        activeTab: String,
    };

    setup() {
        this.stateOptions = STATE_OPTIONS;
        this.local = useState({ search: '' });
    }

    get filteredBoms() {
        const q = this.local.search.toLowerCase().trim();
        if (!q) return this.props.boms;
        return this.props.boms.filter(b => b.name.toLowerCase().includes(q));
    }

    onSearch(ev) {
        this.local.search = ev.target.value;
    }

    onStateChange(ev) {
        this.props.onStateFilter(ev.target.value);
    }

    bomItemClass(id) {
        const active = this.props.selectedBomId === id;
        return [
            'w-full text-left flex items-center gap-2 px-2 py-1.5 rounded-md text-xs mb-0.5 transition-colors',
            active
                ? 'bg-blue-600 text-white font-bold'
                : 'text-gray-400 hover:bg-gray-700 hover:text-gray-200',
        ].join(' ');
    }
}
