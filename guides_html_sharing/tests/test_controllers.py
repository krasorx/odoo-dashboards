# -*- coding: utf-8 -*-
from odoo.tests import HttpCase, tagged


@tagged('post_install', '-at_install', 'guides_html_sharing')
class TestControllers(HttpCase):
    def test_public_route_valid_token(self):
        folder = self.env['guides.folder'].create({'name': 'F'})
        doc = self.env['guides.document'].create({
            'name': 'D', 'folder_id': folder.id,
            'version_ids': [(0, 0, {'content_html': '<h1>PUBLIC</h1>'})]})
        doc.action_enable_share()
        res = self.url_open(f"/guides/public/{doc.share_token}")
        self.assertEqual(res.status_code, 200)
        self.assertIn('PUBLIC', res.text)

    def test_public_route_bad_token(self):
        res = self.url_open("/guides/public/nope-not-real")
        self.assertEqual(res.status_code, 404)
