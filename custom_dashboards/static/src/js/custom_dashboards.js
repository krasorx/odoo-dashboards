/**
 * Custom Dashboards JavaScript
 * Handles chart rendering, data updates, and interactivity
 */

odoo.define('custom_dashboards.CustomDashboard', function (require) {
    'use strict';

    var core = require('web.core');
    var Chart = require('chart.js');
    var widget = require('web.widget');

    var _t = core._t;

    return widget.Widget.extend({
        template: 'custom_dashboards.Dashboard',
        events: {
            'click .refresh-btn': 'onRefresh',
            'click .export-btn': 'onExport',
        },

        start: function () {
            this._super.apply(this, arguments);
            this.$('.chart-container').each(function (i, el) {
                var chart = new Chart(el, {
                    type: 'bar',
                    data: {},
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                    },
                });
            });
        },

        onRefresh: function () {
            this.trigger('reload-data');
        },

        onExport: function (event) {
            event.preventDefault();
            var format = $(event.currentTarget).data('format') || 'pdf';
            window.print();
        },

        destroy: function () {
            this._super.apply(this, arguments);
            Chart.registry.destroy();
        },
    });
});
