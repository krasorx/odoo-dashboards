# -*- coding: utf-8 -*-
from odoo import fields, models

REQUEST_STATES = [('pending', 'Pending'), ('approved', 'Approved'),
                  ('rejected', 'Rejected')]


class GuidesAccessRequest(models.Model):
    _name = 'guides.access.request'
    _description = 'Guide Edit Access Request'
    _order = 'create_date desc'

    document_id = fields.Many2one('guides.document', required=True,
                                  ondelete='cascade')
    user_id = fields.Many2one('res.users', required=True,
                              default=lambda self: self.env.user)
    state = fields.Selection(REQUEST_STATES, default='pending', required=True)
    note = fields.Text()

    def action_approve(self):
        edit_request_type = self.env.ref(
            'guides_html_sharing.mail_activity_edit_request')
        for req in self:
            req.document_id.sudo().write(
                {'editor_ids': [(4, req.user_id.id)]})
            req.state = 'approved'
            req.document_id.activity_ids.filtered(
                lambda a: a.activity_type_id == edit_request_type
            ).action_done()
            req.document_id.message_post(
                body=f"Edit access granted to {req.user_id.name}.",
                partner_ids=[req.user_id.partner_id.id])

    def action_reject(self):
        self.write({'state': 'rejected'})
