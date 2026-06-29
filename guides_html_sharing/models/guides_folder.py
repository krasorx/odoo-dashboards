# -*- coding: utf-8 -*-
from odoo import api, fields, models

ACCESS_LEVELS = [('reader', 'Reader'), ('contributor', 'Contributor')]


class GuidesFolder(models.Model):
    _name = 'guides.folder'
    _description = 'Guide Folder'
    _parent_store = True
    _order = 'complete_name'

    name = fields.Char(required=True)
    parent_id = fields.Many2one('guides.folder', string='Parent Folder',
                                ondelete='cascade', index=True)
    parent_path = fields.Char(index=True)
    complete_name = fields.Char(compute='_compute_complete_name',
                                store=True, recursive=True)
    sequence = fields.Integer(default=10)
    inherit_parent_access = fields.Boolean(
        string='Inherit Parent Access', default=True)
    member_ids = fields.One2many('guides.folder.member', 'folder_id',
                                 string='Members')
    document_ids = fields.One2many('guides.document', 'folder_id',
                                   string='Documents')
    document_count = fields.Integer(compute='_compute_document_count')

    @api.depends('name', 'parent_id.complete_name')
    def _compute_complete_name(self):
        for folder in self:
            if folder.parent_id:
                folder.complete_name = f"{folder.parent_id.complete_name} / {folder.name}"
            else:
                folder.complete_name = folder.name

    def _compute_document_count(self):
        for folder in self:
            folder.document_count = len(folder.document_ids)

    def _get_effective_members(self):
        """Return {user_id(int): 'reader'|'contributor'} for this folder,
        merging ancestor members when inherit_parent_access is set.
        contributor always wins over reader."""
        self.ensure_one()
        result = {}

        def merge(folder):
            for m in folder.member_ids:
                cur = result.get(m.user_id.id)
                if cur != 'contributor':
                    result[m.user_id.id] = m.access_level
            if folder.inherit_parent_access and folder.parent_id:
                merge(folder.parent_id)

        merge(self)
        return result

    def user_can_read(self, user):
        self.ensure_one()
        return user.id in self._get_effective_members()

    def user_can_contribute(self, user):
        self.ensure_one()
        return self._get_effective_members().get(user.id) == 'contributor'


class GuidesFolderMember(models.Model):
    _name = 'guides.folder.member'
    _description = 'Guide Folder Member'

    folder_id = fields.Many2one('guides.folder', required=True,
                                ondelete='cascade')
    user_id = fields.Many2one('res.users', required=True, ondelete='cascade')
    access_level = fields.Selection(ACCESS_LEVELS, required=True,
                                    default='reader')

    _folder_user_uniq = models.Constraint(
        'unique(folder_id, user_id)',
        'This user is already a member of the folder.')
