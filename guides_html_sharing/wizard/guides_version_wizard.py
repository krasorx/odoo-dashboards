# -*- coding: utf-8 -*-
import base64
from odoo import fields, models


class GuidesVersionWizard(models.TransientModel):
    _name = 'guides.version.wizard'
    _description = 'Add Guide Version'

    document_id = fields.Many2one('guides.document', required=True)
    mode = fields.Selection([('inline', 'Edit HTML'),
                             ('upload', 'Upload File')],
                            default='upload', required=True)
    content_html = fields.Text()
    upload_file = fields.Binary(string='HTML File')
    upload_filename = fields.Char()
    changelog = fields.Char()

    def action_save(self):
        self.ensure_one()
        if self.mode == 'upload' and self.upload_file:
            content = base64.b64decode(self.upload_file).decode('utf-8')
            self.document_id.action_add_version(
                content, source='upload',
                original_filename=self.upload_filename,
                changelog=self.changelog)
        else:
            self.document_id.action_add_version(
                self.content_html or '', source='inline',
                changelog=self.changelog)
        return {'type': 'ir.actions.act_window_close'}
