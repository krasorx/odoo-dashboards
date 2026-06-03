/** @odoo-module */
import { Component, xml } from "@odoo/owl";
import { registry } from "@web/core/registry";

const formatters = registry.category("formatters");

export class KpiCard extends Component {
    static template = xml`
        <button
            t-att-class="cardClass"
            t-att-style="props.color ? ('border-color:' + props.color) : ''"
            t-on-click="onClick"
            t-att-disabled="!props.onClick"
            type="button"
        >
            <span class="o_stat_value d-flex align-items-center gap-1">
                <i t-if="props.icon" t-att-class="props.icon"/>
                <span t-esc="formattedValue"/>
            </span>
            <span class="o_stat_text text-muted" t-esc="props.label"/>
        </button>
    `;

    static props = {
        id: { type: [String, Number], optional: true },
        label: String,
        value: [Number, String],
        format: { type: String, optional: true },
        icon: { type: String, optional: true },
        color: { type: String, optional: true },
        active: { type: Boolean, optional: true },
        onClick: { type: Function, optional: true },
    };

    get formattedValue() {
        const { value, format } = this.props;
        if (typeof value === "string" || !format || format === "raw") {
            return value;
        }
        const formatter = formatters.get(format, false);
        try {
            return formatter ? formatter(value) : String(value);
        } catch {
            return String(value);
        }
    }

    get cardClass() {
        const base =
            "o_kanban_card d-flex flex-column align-items-center justify-content-center " +
            "p-3 border rounded me-2 bg-white";
        return this.props.active ? base + " border-primary shadow-sm bg-light" : base;
    }

    onClick() {
        if (this.props.onClick) {
            this.props.onClick(this.props);
        }
    }
}
