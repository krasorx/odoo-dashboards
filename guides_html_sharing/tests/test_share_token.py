# -*- coding: utf-8 -*-
from datetime import datetime, timedelta
from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install', 'guides_html_sharing')
class TestShareToken(TransactionCase):
    def setUp(self):
        super().setUp()
        folder = self.env['guides.folder'].create({'name': 'F'})
        self.doc = self.env['guides.document'].create({
            'name': 'D', 'folder_id': folder.id,
            'version_ids': [(0, 0, {'content_html': '<p>hi</p>'})]})

    def test_enable_generates_token(self):
        self.doc.action_enable_share()
        self.assertTrue(self.doc.share_token)
        self.assertTrue(self.doc.share_active)
        self.assertTrue(self.doc._is_share_valid())

    def test_lookup_by_token(self):
        self.doc.action_enable_share()
        found = self.env['guides.document']._get_valid_shared_document(
            self.doc.share_token)
        self.assertEqual(found, self.doc)

    def test_revoke_invalidates(self):
        self.doc.action_enable_share()
        token = self.doc.share_token
        self.doc.action_revoke_share()
        self.assertFalse(self.doc._is_share_valid())
        self.assertFalse(
            self.env['guides.document']._get_valid_shared_document(token))

    def test_expiry(self):
        self.doc.action_enable_share()
        self.doc.share_expiry = datetime.now() - timedelta(days=1)
        self.assertFalse(self.doc._is_share_valid())
