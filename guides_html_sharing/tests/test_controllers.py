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

    def test_render_route_authenticated(self):
        g_user = self.env.ref('guides_html_sharing.group_guides_user')
        g_internal = self.env.ref('base.group_user')
        user = self.env['res.users'].create({
            'name': 'Reader', 'login': 'reader_ctrl', 'password': 'reader_ctrl',
            'email': 'reader@x.com',
            'group_ids': [(6, 0, [g_internal.id, g_user.id])]})
        folder = self.env['guides.folder'].create({
            'name': 'CtrlF',
            'member_ids': [(0, 0, {'user_id': user.id,
                                   'access_level': 'reader'})]})
        doc = self.env['guides.document'].create({
            'name': 'D', 'folder_id': folder.id,
            'version_ids': [(0, 0, {'content_html': '<h1>BACKEND</h1>'})]})
        self.authenticate('reader_ctrl', 'reader_ctrl')
        res = self.url_open(f"/guides/render/{doc.id}")
        self.assertEqual(res.status_code, 200)
        self.assertIn('BACKEND', res.text)
