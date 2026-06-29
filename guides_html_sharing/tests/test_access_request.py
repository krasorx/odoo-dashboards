# -*- coding: utf-8 -*-
from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install', 'guides_html_sharing')
class TestAccessRequest(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        g_user = cls.env.ref('guides_html_sharing.group_guides_user')
        g_internal = cls.env.ref('base.group_user')
        cls.owner = cls.env['res.users'].create({
            'name': 'Owner', 'login': 'owner_g', 'email': 'o@x.com',
            'group_ids': [(6, 0, [g_internal.id, g_user.id])]})
        cls.req_user = cls.env['res.users'].create({
            'name': 'Req', 'login': 'req_g', 'email': 'r@x.com',
            'group_ids': [(6, 0, [g_internal.id, g_user.id])]})
        folder = cls.env['guides.folder'].create({'name': 'F'})
        cls.doc = cls.env['guides.document'].create({
            'name': 'D', 'folder_id': folder.id, 'owner_id': cls.owner.id})

    def test_request_creates_activity(self):
        req = self.doc.with_user(self.req_user).action_request_edit_access(
            note='please')
        self.assertEqual(req.state, 'pending')
        activities = self.doc.activity_ids.filtered(
            lambda a: a.user_id == self.owner)
        self.assertTrue(activities)

    def test_approve_adds_editor(self):
        req = self.doc.with_user(self.req_user).action_request_edit_access()
        req.with_user(self.owner).action_approve()
        self.assertEqual(req.state, 'approved')
        self.assertIn(self.req_user, self.doc.editor_ids)
