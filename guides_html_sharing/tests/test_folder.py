# -*- coding: utf-8 -*-
from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install', 'guides_html_sharing')
class TestGuidesFolder(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Folder = cls.env['guides.folder']
        cls.alice = cls.env['res.users'].create({
            'name': 'Alice', 'login': 'alice_guides', 'email': 'a@x.com'})
        cls.bob = cls.env['res.users'].create({
            'name': 'Bob', 'login': 'bob_guides', 'email': 'b@x.com'})

    def test_complete_name(self):
        root = self.Folder.create({'name': 'Clients'})
        child = self.Folder.create({'name': 'Acme', 'parent_id': root.id})
        self.assertEqual(child.complete_name, 'Clients / Acme')

    def test_effective_members_inherit(self):
        root = self.Folder.create({
            'name': 'Root',
            'member_ids': [(0, 0, {'user_id': self.alice.id,
                                   'access_level': 'contributor'})],
        })
        child = self.Folder.create({
            'name': 'Child', 'parent_id': root.id,
            'inherit_parent_access': True,
            'member_ids': [(0, 0, {'user_id': self.bob.id,
                                   'access_level': 'reader'})],
        })
        self.assertTrue(child.user_can_contribute(self.alice))
        self.assertTrue(child.user_can_read(self.bob))
        self.assertFalse(child.user_can_contribute(self.bob))

    def test_no_inherit(self):
        root = self.Folder.create({
            'name': 'Root2',
            'member_ids': [(0, 0, {'user_id': self.alice.id,
                                   'access_level': 'contributor'})],
        })
        child = self.Folder.create({
            'name': 'Child2', 'parent_id': root.id,
            'inherit_parent_access': False,
        })
        self.assertFalse(child.user_can_read(self.alice))
