/** @odoo-module */
import { Component, useState, onMounted, onWillUnmount, xml } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";
import { BomSidebar } from "./BomSidebar";
import { BomStructureView } from "./BomStructureView";
import { BomMoView } from "./BomMoView";

export class BomDashboard extends Component {
    static template = xml`
        <div class="flex bg-gray-50 font-sans overflow-hidden" style="height:100vh;">

            <BomSidebar
                boms="state.boms"
                selectedBomId="state.selectedBomId"
                onSelect.bind="selectBom"
                stateFilter="state.stateFilter"
                onStateFilter.bind="setStateFilter"
                activeTab="state.activeTab"
            />

            <div class="flex-1 flex flex-col min-w-0 overflow-hidden">

                <!-- Tabs header -->
                <div class="bg-white border-b border-gray-200 px-4 flex items-center flex-shrink-0 shadow-sm" style="min-height:44px;">
                    <button t-att-class="tabClass('structure')" t-on-click="() => this.setTab('structure')">
                        📋 Estructura BOM
                    </button>
                    <button t-att-class="tabClass('mos')" t-on-click="() => this.setTab('mos')">
                        🏭 MOs Activas
                    </button>
                    <div class="ml-auto flex items-center gap-2 pr-1">
                        <t t-if="state.selectedBomId">
                            <span class="text-xs text-gray-500 font-semibold truncate max-w-xs" t-esc="selectedBomName"/>
                            <t t-if="state.activeTab === 'mos' and moCount > 0">
                                <span class="text-xs bg-amber-100 text-amber-800 px-2 py-0.5 rounded-full font-bold flex-shrink-0">
                                    <t t-esc="moCount"/> MOs
                                </span>
                            </t>
                            <t t-elif="state.activeTab === 'structure' and levelCount > 0">
                                <span class="text-xs bg-blue-100 text-blue-800 px-2 py-0.5 rounded-full font-bold flex-shrink-0">
                                    <t t-esc="levelCount"/> niveles
                                </span>
                            </t>
                        </t>
                        <t t-if="state.loading">
                            <span class="text-gray-400 text-xs animate-pulse ml-1">↻</span>
                        </t>
                    </div>
                </div>

                <!-- Content area -->
                <div class="flex-1 overflow-hidden">
                    <t t-if="!state.selectedBomId">
                        <div class="flex items-center justify-center h-full text-gray-300 text-sm select-none">
                            Seleccioná un BOM en el panel izquierdo
                        </div>
                    </t>
                    <t t-elif="state.loading and !state.bomTree">
                        <div class="flex items-center justify-center h-full text-gray-300 text-sm select-none animate-pulse">
                            Cargando...
                        </div>
                    </t>
                    <t t-elif="state.activeTab === 'structure'">
                        <BomStructureView
                            columns="visibleColumns"
                            hiddenCount="hiddenLevelsCount"
                            onShowAll.bind="showAllLevels"
                        />
                    </t>
                    <t t-else="">
                        <BomMoView
                            columns="visibleColumns"
                            hiddenCount="hiddenLevelsCount"
                            onShowAll.bind="showAllLevels"
                            loading="state.loading"
                        />
                    </t>
                </div>

            </div>
        </div>
    `;

    static components = { BomSidebar, BomStructureView, BomMoView };

    setup() {
        this.rpc = useService("rpc");
        this.state = useState({
            boms: [],
            selectedBomId: false,
            activeTab: 'structure',
            bomTree: null,
            stateFilter: false,
            showAll: false,
            loading: false,
        });
        this._timer = null;

        onMounted(async () => {
            this._injectTailwind();
            await this._loadBoms();
        });

        onWillUnmount(() => {
            if (this._timer) clearInterval(this._timer);
        });
    }

    // Dev-only: Tailwind CDN for rapid iteration. For production, replace with
    // a compiled CSS asset shipped in web.assets_backend instead of this script.
    _injectTailwind() {
        if (!document.querySelector('#bom-tw-cdn')) {
            const s = document.createElement('script');
            s.id = 'bom-tw-cdn';
            s.src = 'https://cdn.tailwindcss.com';
            document.head.appendChild(s);
        }
    }

    async _loadBoms() {
        const boms = await this.rpc('/bom/dashboard/boms', {});
        this.state.boms = boms || [];
        if (this.state.boms.length && !this.state.selectedBomId) {
            await this.selectBom(this.state.boms[0].id);
        }
    }

    async loadData() {
        if (!this.state.selectedBomId) return;
        this.state.loading = true;
        try {
            const result = await this.rpc('/bom/dashboard/data', {
                bom_id: this.state.selectedBomId,
                state_filter: this.state.stateFilter || false,
            });
            this.state.boms = result.boms || this.state.boms;
            this.state.bomTree = result.tree || null;
        } catch (err) {
            console.error('[BomDashboard] Error loading data:', err);
        } finally {
            this.state.loading = false;
        }
    }

    async selectBom(id) {
        this.state.selectedBomId = id;
        this.state.showAll = false;
        this.state.bomTree = null;
        if (this._timer) clearInterval(this._timer);
        await this.loadData();
        // Only auto-refresh in MOs tab
        this._timer = setInterval(() => {
            if (this.state.activeTab === 'mos') this.loadData();
        }, 30_000);
    }

    setTab(tab) {
        this.state.activeTab = tab;
    }

    setStateFilter(val) {
        this.state.stateFilter = val || false;
        this.loadData();
    }

    showAllLevels() {
        this.state.showAll = true;
    }

    tabClass(tab) {
        const active = this.state.activeTab === tab;
        return [
            'px-4 py-3 text-xs font-semibold border-b-2 transition-colors flex-shrink-0',
            active
                ? 'text-blue-600 border-blue-500'
                : 'text-gray-400 border-transparent hover:text-gray-600',
        ].join(' ');
    }

    get selectedBomName() {
        const bom = this.state.boms.find(b => b.id === this.state.selectedBomId);
        return bom ? bom.name : '';
    }

    // Flatten nested tree into columns: columns[level] = [{parentName, items}]
    get allColumns() {
        if (!this.state.bomTree) return [];
        const columns = [];

        const traverse = (node, parentName) => {
            const lvl = node.level;
            if (!columns[lvl]) columns[lvl] = [];
            let group = columns[lvl].find(g => g.parentName === parentName);
            if (!group) {
                group = { parentName, items: [] };
                columns[lvl].push(group);
            }
            group.items.push(node);
            for (const child of node.children || []) {
                traverse(child, node.product_name);
            }
        };

        traverse(this.state.bomTree, null);
        return columns;
    }

    get visibleColumns() {
        const all = this.allColumns;
        return this.state.showAll ? all : all.slice(0, 5);
    }

    get hiddenLevelsCount() {
        return Math.max(0, this.allColumns.length - 5);
    }

    get levelCount() {
        return this.allColumns.length;
    }

    get moCount() {
        if (!this.state.bomTree) return 0;
        let count = 0;
        const sum = (node) => {
            count += (node.mos || []).length;
            for (const c of node.children || []) sum(c);
        };
        sum(this.state.bomTree);
        return count;
    }
}
