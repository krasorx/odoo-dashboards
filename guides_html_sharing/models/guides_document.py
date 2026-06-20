# -*- coding: utf-8 -*-
import secrets

from odoo import api, fields, models
from odoo.exceptions import AccessError


class GuidesDocument(models.Model):
    _name = 'guides.document'
    _description = 'Guide Document'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'name'

    name = fields.Char(required=True, tracking=True)
    active = fields.Boolean(default=True)
    folder_id = fields.Many2one('guides.folder', string='Folder',
                                required=True, tracking=True, index=True)
    owner_id = fields.Many2one('res.users', string='Owner',
                               default=lambda self: self.env.user,
                               tracking=True, index=True)
    editor_ids = fields.Many2many('res.users', 'guides_document_editor_rel',
                                  'document_id', 'user_id', string='Editors')
    tag_ids = fields.Many2many('guides.tag', string='Tags')
    project_id = fields.Many2one('project.project', string='Project')
    task_id = fields.Many2one('project.task', string='Task')

    version_ids = fields.One2many('guides.document.version', 'document_id',
                                  string='Versions')
    active_version_id = fields.Many2one('guides.document.version',
                                        string='Current Version')
    version_count = fields.Integer(compute='_compute_version_count')
    content_html = fields.Text(related='active_version_id.content_html',
                               string='Current HTML', readonly=True)

    share_token = fields.Char(copy=False, index=True, readonly=True)
    share_active = fields.Boolean(string='Public Link Enabled', default=False)
    share_expiry = fields.Datetime(string='Link Expiry')

    @api.depends('version_ids')
    def _compute_version_count(self):
        for doc in self:
            doc.version_count = len(doc.version_ids)

    @api.onchange('task_id')
    def _onchange_task_id(self):
        if self.task_id:
            self.project_id = self.task_id.project_id

    @api.model_create_multi
    def create(self, vals_list):
        is_admin = self.env.is_superuser() or self.env.user.has_group(
            'guides_html_sharing.group_guides_admin')
        if not is_admin:
            for vals in vals_list:
                folder = self.env['guides.folder'].browse(vals.get('folder_id'))
                if not folder or not folder.sudo().user_can_contribute(self.env.user):
                    raise AccessError(
                        "You don't have contributor rights on this folder.")
        docs = super().create(vals_list)
        for doc in docs:
            # Number any versions created inline, and set the latest active.
            versions = doc.version_ids.sorted('id')
            for idx, v in enumerate(versions, start=1):
                v.version_number = idx
            if versions and not doc.active_version_id:
                doc.active_version_id = versions[-1]
        return docs

    def _next_version_number(self):
        self.ensure_one()
        return max(self.version_ids.mapped('version_number') or [0]) + 1

    def action_add_version(self, content_html, source='inline',
                           original_filename=False, changelog=False):
        self.ensure_one()
        version = self.env['guides.document.version'].create({
            'document_id': self.id,
            'version_number': self._next_version_number(),
            'content_html': content_html,
            'source': source,
            'original_filename': original_filename,
            'changelog': changelog,
        })
        self.active_version_id = version
        self.message_post(body=f"New version v{version.version_number} added.")
        return version

    def action_restore_version(self, version):
        self.ensure_one()
        return self.action_add_version(
            version.content_html, source=version.source,
            changelog=f"Restored from v{version.version_number}")

    def action_enable_share(self):
        self.ensure_one()
        if not self.share_token:
            self.share_token = secrets.token_urlsafe(24)
        self.share_active = True
        return f"{self.get_base_url()}/guides/public/{self.share_token}"

    def action_regenerate_token(self):
        self.ensure_one()
        self.share_token = secrets.token_urlsafe(24)
        return self.action_enable_share()

    def action_revoke_share(self):
        self.share_active = False

    def _is_share_valid(self):
        self.ensure_one()
        if not self.share_active or not self.share_token:
            return False
        if self.share_expiry and self.share_expiry < fields.Datetime.now():
            return False
        return True

    @api.model
    def _get_valid_shared_document(self, token):
        if not token:
            return self.browse()
        doc = self.sudo().search([('share_token', '=', token)], limit=1)
        return doc if (doc and doc._is_share_valid()) else self.browse()

    def action_request_edit_access(self, note=False):
        self.ensure_one()
        requester = self.env.user
        doc_sudo = self.sudo()
        request = self.env['guides.access.request'].sudo().create({
            'document_id': self.id,
            'user_id': requester.id,
            'note': note,
        })
        doc_sudo.activity_schedule(
            'guides_html_sharing.mail_activity_edit_request',
            user_id=doc_sudo.owner_id.id,
            note=f"{requester.name} requested edit access. {note or ''}",
            summary='Edit access requested')
        return request
