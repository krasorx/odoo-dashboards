# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import http, _
import json
from datetime import datetime

class CustomDashboard(http.Controller):
    @http.route('/my/invoices/monthly', type='json', auth="user", website=True)
    def invoices_monthly(self, date=None):
        if not date:
            today = datetime.now()
            start_of_month = today.replace(day=1)
            date = start_of_month.strftime('%Y-%m-%d')
        
        invoices = self.env['account.move'].sudo().search([
            ('move_type', '=', 'out_invoice'),
            ('invoice_date', '>=', date),
            ('state', '=', 'posted')
        ])
        
        return {
            'invoiced_amount': sum(invoices.mapped('amount_total_signed')),
            'invoice_count': len(invoices),
        }

    @http.route('/my/mps/completed', type='json', auth="user", website=True)
    def mps_completed(self, date=None):
        if not date:
            today = datetime.now().strftime('%Y-%m-%d')
            date = today
        
        mps = self.env['mrp.production'].sudo().search([
            ('state', '=', 'done'),
            ('date_finished', '>=', date)
        ], limit=100)
        
        return {
            'count': len(mps),
            'total_qty': sum(mps.mapped('product_id.qty_done')),
            'data': mps.read(['name', 'product_id:read,name', 'qty_done']),
        }

    @http.route('/my/sales/pending', type='json', auth="user", website=True)
    def sales_pending(self, date=None):
        if not date:
            today = datetime.now().strftime('%Y-%m-%d')
            date = today
        
        sales = self.env['sale.order'].sudo().search([
            ('state', '=', 'sale'),
            ('date_order', '>=', date)
        ], limit=100)
        
        return {
            'count': len(sales),
            'amount': sum(sales.mapped('amount_total')),
        }

    @http.route('/my/overdue/invoices', type='json', auth="user", website=True)
    def overdue_invoices(self):
        today = datetime.now().strftime('%Y-%m-%d')
        
        overdue = self.env['account.move'].sudo().search([
            ('move_type', '=', 'out_invoice'),
            ('state', '=', 'posted'),
            ('reconciliation_state', '=', 'none'),
            ('invoice_date', '<', today),
            '|',
            ('reconciled_partial', '=', 0.0),
            ('reconciled_partial', '>', 1.0)
        ], order='date_invoice asc', limit=50)
        
        return {
            'count': len(overdue),
            'data': overdue.read(['name', 'partner_id:read,name', 'amount_total_signed', 'date_due']),
        }

    @http.route('/my/top/products', type='json', auth="user", website=True)
    def top_products(self, date=None, limit=10):
        if not date:
            today = datetime.now()
            start_of_month = today.replace(day=1)
            date = start_of_month.strftime('%Y-%m-%d')
        
        lines = self.env['account.move.line'].sudo().search([
            ('product_id', '!=', False),
            ('move_type', '=', 'out_invoice'),
            ('invoice_date', '>=', date)
        ], order='qty_done desc', limit=limit)
        
        return {
            'data': lines.read(['product_id:read,name', 'product_uom_qty', 'price_unit']),
        }

    @http.route('/custom-dashboards/dashboard', type="http", auth="user", website=True)
    def dashboard(self):
        return self.render_template('custom_dashboards_dashboard', name='Custom Dashboard')
