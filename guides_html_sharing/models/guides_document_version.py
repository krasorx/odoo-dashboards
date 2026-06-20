# -*- coding: utf-8 -*-
from odoo import api, fields, models

VERSION_SOURCES = [('inline', 'Inline Edit'), ('upload', 'File Upload')]


class GuidesDocumentVersion(models.Model):
    _name = 'guides.document.version'
    _description = 'Guide Document Version'
    _order = 'version_number desc'

    document_id = fields.Many2one('guides.document', required=True,
                                  ondelete='cascade', index=True)
    version_number = fields.Integer(string='Version', default=1)
    content_html = fields.Text(string='HTML Content')
    source = fields.Selection(VERSION_SOURCES, default='inline')
    original_filename = fields.Char()
    changelog = fields.Char()

    @api.depends('version_number')
    def _compute_display_name(self):
        for version in self:
            version.display_name = f"v{version.version_number}"
