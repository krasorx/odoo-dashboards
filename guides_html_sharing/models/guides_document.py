# -*- coding: utf-8 -*-
from odoo import api, fields, models


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
