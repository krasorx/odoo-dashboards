# -*- coding: utf-8 -*-
from odoo.tests import TransactionCase, tagged
from psycopg2 import IntegrityError
from odoo.tools import mute_logger


@tagged('post_install', '-at_install', 'guides_html_sharing')
class TestGuidesTag(TransactionCase):
    def test_create_tag(self):
        tag = self.env['guides.tag'].create({'name': 'Configuration'})
        self.assertEqual(tag.name, 'Configuration')

    @mute_logger('odoo.sql_db')
    def test_tag_name_unique(self):
        self.env['guides.tag'].create({'name': 'Dup'})
        with self.assertRaises(IntegrityError):
            self.env['guides.tag'].create({'name': 'Dup'})
            self.env.flush_all()
