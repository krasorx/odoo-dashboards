# -*- coding: utf-8 -*-
from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install', 'guides_html_sharing')
class TestProjectIntegration(TransactionCase):
    def test_task_guide_count(self):
        project = self.env['project.project'].create({'name': 'P'})
        task = self.env['project.task'].create(
            {'name': 'T', 'project_id': project.id})
        folder = self.env['guides.folder'].create({'name': 'F'})
        self.env['guides.document'].create({
            'name': 'Guide', 'folder_id': folder.id, 'task_id': task.id})
        self.assertEqual(task.guide_document_count, 1)
        action = task.action_view_guides()
        self.assertEqual(action['res_model'], 'guides.document')
        self.assertEqual(action['domain'], [('task_id', '=', task.id)])
