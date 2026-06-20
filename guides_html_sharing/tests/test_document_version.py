# -*- coding: utf-8 -*-
from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install', 'guides_html_sharing')
class TestDocumentVersion(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.folder = cls.env['guides.folder'].create({'name': 'F'})

    def _new_doc(self):
        return self.env['guides.document'].create({
            'name': 'How to configure X',
            'folder_id': self.folder.id,
            'version_ids': [(0, 0, {'content_html': '<h1>v1</h1>',
                                    'source': 'inline'})],
        })

    def test_first_version_active(self):
        doc = self._new_doc()
        self.assertEqual(doc.version_count, 1)
        self.assertEqual(doc.active_version_id.version_number, 1)
        self.assertEqual(doc.content_html, '<h1>v1</h1>')

    def test_add_version_becomes_active(self):
        doc = self._new_doc()
        v2 = doc.action_add_version('<h1>v2</h1>', source='upload',
                                    original_filename='x.html')
        self.assertEqual(v2.version_number, 2)
        self.assertEqual(doc.active_version_id, v2)
        self.assertEqual(doc.content_html, '<h1>v2</h1>')
        self.assertEqual(doc.version_count, 2)

    def test_restore_creates_new_version(self):
        doc = self._new_doc()
        v1 = doc.active_version_id
        doc.action_add_version('<h1>v2</h1>')
        v3 = doc.action_restore_version(v1)
        self.assertEqual(v3.version_number, 3)
        self.assertEqual(doc.content_html, '<h1>v1</h1>')

    def test_task_sets_project(self):
        project = self.env['project.project'].create({'name': 'P'})
        task = self.env['project.task'].create(
            {'name': 'T', 'project_id': project.id})
        doc = self.env['guides.document'].new({'task_id': task.id})
        doc._onchange_task_id()
        self.assertEqual(doc.project_id, project)
