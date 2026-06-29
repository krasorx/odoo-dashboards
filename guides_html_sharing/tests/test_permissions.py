# -*- coding: utf-8 -*-
from odoo.tests import TransactionCase, tagged
from odoo.exceptions import AccessError
from odoo.tools import mute_logger


@tagged('post_install', '-at_install', 'guides_html_sharing')
class TestPermissions(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        g_user = cls.env.ref('guides_html_sharing.group_guides_user')
        g_view = cls.env.ref('guides_html_sharing.group_guides_viewer')
        g_internal = cls.env.ref('base.group_user')
        cls.contrib = cls.env['res.users'].create({
            'name': 'Contrib', 'login': 'contrib_g', 'email': 'c@x.com',
            'group_ids': [(6, 0, [g_internal.id, g_user.id])]})
        cls.viewer = cls.env['res.users'].create({
            'name': 'Viewer', 'login': 'viewer_g', 'email': 'v@x.com',
            'group_ids': [(6, 0, [g_internal.id, g_view.id])]})
        cls.folder = cls.env['guides.folder'].create({
            'name': 'Shared',
            'member_ids': [(0, 0, {'user_id': cls.contrib.id,
                                   'access_level': 'contributor'})]})

    def test_contributor_can_create_in_folder(self):
        doc = self.env['guides.document'].with_user(self.contrib).create({
            'name': 'Doc', 'folder_id': self.folder.id,
            'version_ids': [(0, 0, {'content_html': '<p>x</p>'})]})
        self.assertTrue(doc.id)

    @mute_logger('odoo.addons.base.models.ir_rule', 'odoo.models')
    def test_non_contributor_cannot_create(self):
        other = self.env['guides.folder'].create({'name': 'Private'})
        with self.assertRaises(AccessError):
            self.env['guides.document'].with_user(self.contrib).create({
                'name': 'Nope', 'folder_id': other.id,
                'version_ids': [(0, 0, {'content_html': '<p>x</p>'})]})

    @mute_logger('odoo.addons.base.models.ir_rule', 'odoo.models')
    def test_viewer_sees_only_followed(self):
        doc = self.env['guides.document'].create({
            'name': 'Secret', 'folder_id': self.folder.id})
        with self.assertRaises(AccessError):
            doc.with_user(self.viewer).read(['name'])
        doc.message_subscribe(partner_ids=[self.viewer.partner_id.id])
        self.assertEqual(
            doc.with_user(self.viewer).read(['name'])[0]['name'], 'Secret')
