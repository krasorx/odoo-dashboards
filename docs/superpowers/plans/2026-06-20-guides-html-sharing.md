# Guides HTML Sharing Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the `guides_html_sharing` Odoo addon: an internal tool to upload, organize (folders/tags), version, permission, and share AI-generated HTML documentation pages, rendered in a sandboxed iframe with a custom OWL browser and a tokenized public link.

**Architecture:** A single Odoo 19 addon in the `odoo-dashboards` repo. Server side: `guides.folder` (+ per-folder ACL lines), `guides.document` (mail.thread head), `guides.document.version` (immutable HTML snapshots), `guides.tag`, `guides.access.request`, plus `project.task` integration. HTTP controllers serve version HTML into a sandboxed iframe (backend, `auth='user'`) and a tokenized public page (`auth='public'`). Front end: an OWL client action with a folder tree + document list + iframe viewer.

**Tech Stack:** Python (Odoo ORM, `mail`/`project`/`portal` mixins), Odoo HTTP controllers, OWL 2 (`@odoo/owl`, `@web/core/registry`), QWeb, XML data/views.

## Global Constraints

- Odoo version: `19.0`; manifest version string `19.0.1.0.0`.
- License: `LGPL-3`.
- Addon path: `addons/odoo-dashboards/guides_html_sharing/`.
- Container service: `odoo` (container `odoo_ee_19`); database: `postgres`.
- HTML is a single self-contained file (inline/CDN CSS+JS); no external asset bundles.
- Backend iframe uses `sandbox="allow-scripts"` (no `allow-same-origin`); HTML responses carry a restrictive `Content-Security-Policy`.
- Three security groups, implied chain: `group_guides_viewer` ⊂ `group_guides_user` ⊂ `group_guides_admin`.
- OWL modules start with `/** @odoo-module */`; import from `@odoo/owl` and `@web/...` (follow `kpi_widgets` pattern, NOT the legacy `odoo.define` style in `custom_dashboards`).
- All test tags use `/guides_html_sharing`.

### Standard test command

From `/home/krasorx/server/odoo-19-ee`, after the module exists, install once with `-i` then use `-u` for reruns:

```bash
docker compose exec -T odoo odoo -d postgres -i guides_html_sharing \
  --test-enable --test-tags /guides_html_sharing \
  --stop-after-init --no-http --log-level=test 2>&1 | tail -50
```

Pass criterion: output ends with `0 failed, 0 error(s)` (and no traceback).

### File structure

```
guides_html_sharing/
  __init__.py
  __manifest__.py
  models/
    __init__.py
    guides_tag.py
    guides_folder.py            # guides.folder + guides.folder.member
    guides_document.py          # guides.document (+ share token + access-request methods)
    guides_document_version.py
    guides_access_request.py
    project_task.py
  controllers/
    __init__.py
    main.py
  security/
    guides_security.xml         # groups + record rules
    ir.model.access.csv
  data/
    guides_data.xml             # ir.sequence, mail.activity.type
  views/
    guides_menus.xml
    guides_folder_views.xml
    guides_tag_views.xml
    guides_document_views.xml
    project_task_views.xml
  static/src/guides_browser/
    guides_browser.js
    guides_browser.xml
    guides_browser.scss
  tests/
    __init__.py
    test_folder.py
    test_document_version.py
    test_permissions.py
    test_share_token.py
    test_access_request.py
    test_project.py
    test_controllers.py
```

---

### Task 1: Addon scaffold + infrastructure wiring

**Files:**
- Create: `addons/odoo-dashboards/guides_html_sharing/__init__.py`
- Create: `addons/odoo-dashboards/guides_html_sharing/__manifest__.py`
- Create: `addons/odoo-dashboards/guides_html_sharing/models/__init__.py` (empty for now)
- Modify: `/home/krasorx/server/odoo-19-ee/odoo.conf` (add path to `addons_path`)

**Interfaces:**
- Produces: an installable empty module `guides_html_sharing`.

- [ ] **Step 1: Create `__init__.py`**

```python
# -*- coding: utf-8 -*-
from . import models
```

- [ ] **Step 2: Create `models/__init__.py`** (empty placeholder)

```python
# -*- coding: utf-8 -*-
```

- [ ] **Step 3: Create `__manifest__.py`**

```python
# -*- coding: utf-8 -*-
{
    'name': 'Guides HTML Sharing',
    'version': '19.0.1.0.0',
    'category': 'Productivity/Documentation',
    'summary': 'Upload, organize, version and share AI-generated HTML documentation',
    'depends': ['web', 'mail', 'project', 'portal'],
    'data': [
        'security/guides_security.xml',
        'security/ir.model.access.csv',
        'data/guides_data.xml',
        'views/guides_tag_views.xml',
        'views/guides_folder_views.xml',
        'views/guides_document_views.xml',
        'views/project_task_views.xml',
        'views/guides_menus.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'guides_html_sharing/static/src/guides_browser/guides_browser.scss',
            'guides_html_sharing/static/src/guides_browser/guides_browser.js',
            'guides_html_sharing/static/src/guides_browser/guides_browser.xml',
        ],
    },
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}
```

> NOTE: data files listed here are created in later tasks. Until then, comment out
> lines for files that don't exist yet OR build the data files first. To keep each
> task independently installable, after creating each data/view file uncomment its
> line. For Task 1's install check, temporarily set `'data': []` and `'assets': {}`,
> then restore the full lists as files are added. Record this in the commit message.

- [ ] **Step 4: Add addon path to `odoo.conf`**

Edit `/home/krasorx/server/odoo-19-ee/odoo.conf` — append `/mnt/extra-addons/odoo-dashboards` to the `addons_path` line:

```
addons_path = /mnt/extra-addons/ntsystemwork/nt-addons, /mnt/extra-addons/ee/enterprise,  /mnt/extra-addons/random-addons, /mnt/extra-addons/odoo-dashboards
```

> The container reads `odoo.conf` via a templated entrypoint; restart so the new
> addons_path is picked up: `docker compose restart odoo` (run from the project root).

- [ ] **Step 5: Restart and verify module is detected**

```bash
cd /home/krasorx/server/odoo-19-ee
docker compose restart odoo
docker compose exec -T odoo odoo -d postgres -i guides_html_sharing \
  --stop-after-init --no-http --log-level=info 2>&1 | tail -20
```

Expected: log shows `Module guides_html_sharing: loading ...` and `Modules loaded.` with no traceback.

- [ ] **Step 6: Commit**

```bash
cd /home/krasorx/server/odoo-19-ee/addons/odoo-dashboards
git add guides_html_sharing
git -C /home/krasorx/server/odoo-19-ee add odoo.conf
git commit -m "feat(guides): scaffold guides_html_sharing addon + addons_path wiring"
```

> The `odoo.conf` lives in the parent (non-git) project dir; commit only the addon
> to the `odoo-dashboards` repo. Note the odoo.conf change in the commit body.

---

### Task 2: `guides.tag` model

**Files:**
- Create: `guides_html_sharing/models/guides_tag.py`
- Modify: `guides_html_sharing/models/__init__.py`
- Modify: `guides_html_sharing/security/ir.model.access.csv` (create in this task)
- Create: `guides_html_sharing/tests/__init__.py`, `guides_html_sharing/tests/test_folder.py` (tag test lives here initially; rename concept: use `test_document_version.py` later). Use `tests/test_tag.py`.
- Test: `guides_html_sharing/tests/test_tag.py`

**Interfaces:**
- Produces: model `guides.tag` with fields `name` (Char, required, unique), `color` (Integer).

- [ ] **Step 1: Write the failing test** — `tests/__init__.py`:

```python
# -*- coding: utf-8 -*-
from . import test_tag
```

`tests/test_tag.py`:

```python
# -*- coding: utf-8 -*-
from odoo.tests import TransactionCase, tagged
from odoo.exceptions import ValidationError
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
```

- [ ] **Step 2: Run test to verify it fails**

```bash
docker compose exec -T odoo odoo -d postgres -i guides_html_sharing \
  --test-enable --test-tags /guides_html_sharing --stop-after-init --no-http 2>&1 | tail -30
```

Expected: FAIL — `guides.tag` model does not exist.

- [ ] **Step 3: Create `models/guides_tag.py`**

```python
# -*- coding: utf-8 -*-
from odoo import fields, models


class GuidesTag(models.Model):
    _name = 'guides.tag'
    _description = 'Guide Tag'
    _order = 'name'

    name = fields.Char(required=True)
    color = fields.Integer(string='Color')

    _sql_constraints = [
        ('name_uniq', 'unique(name)', 'A tag with this name already exists.'),
    ]
```

- [ ] **Step 4: Register model** — `models/__init__.py`:

```python
# -*- coding: utf-8 -*-
from . import guides_tag
```

- [ ] **Step 5: Create `security/ir.model.access.csv`** (groups not defined yet — grant to base.group_user for now; tightened in Task 5):

```csv
id,name,model_id:id,group_id:id,perm_read,perm_write,perm_create,perm_unlink
access_guides_tag_user,guides.tag user,model_guides_tag,base.group_user,1,1,1,1
```

- [ ] **Step 6: Restore manifest `data`/`assets`** for files that now exist. Set:

```python
    'data': [
        'security/ir.model.access.csv',
    ],
```

- [ ] **Step 7: Run tests to verify they pass**

```bash
docker compose exec -T odoo odoo -d postgres -u guides_html_sharing \
  --test-enable --test-tags /guides_html_sharing --stop-after-init --no-http 2>&1 | tail -30
```

Expected: PASS — `0 failed, 0 error(s)`.

- [ ] **Step 8: Commit**

```bash
cd /home/krasorx/server/odoo-19-ee/addons/odoo-dashboards
git add guides_html_sharing && git commit -m "feat(guides): add guides.tag model"
```

---

### Task 3: `guides.folder` + `guides.folder.member` (ACL lines)

**Files:**
- Create: `guides_html_sharing/models/guides_folder.py`
- Modify: `guides_html_sharing/models/__init__.py`
- Modify: `guides_html_sharing/security/ir.model.access.csv`
- Modify: `guides_html_sharing/tests/__init__.py`
- Test: `guides_html_sharing/tests/test_folder.py`

**Interfaces:**
- Produces:
  - `guides.folder`: `name` (Char req), `parent_id` (Many2one self), `parent_path` (Char index, `_parent_store`), `complete_name` (Char computed stored), `sequence` (Integer), `inherit_parent_access` (Boolean, default True), `member_ids` (One2many `guides.folder.member`), method `_get_effective_members()` → returns `{user_id: 'reader'|'contributor'}` dict (contributor wins over reader; ancestors merged when inheriting), method `user_can_contribute(user)` → bool, `user_can_read(user)` → bool.
  - `guides.folder.member`: `folder_id` (Many2one req), `user_id` (Many2one res.users req), `access_level` (Selection `[('reader',...),('contributor',...)]` default reader).

- [ ] **Step 1: Write the failing test** — add `from . import test_folder` to `tests/__init__.py`; `tests/test_folder.py`:

```python
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
```

- [ ] **Step 2: Run test to verify it fails**

```bash
docker compose exec -T odoo odoo -d postgres -u guides_html_sharing \
  --test-enable --test-tags /guides_html_sharing --stop-after-init --no-http 2>&1 | tail -30
```

Expected: FAIL — `guides.folder` not found.

- [ ] **Step 3: Create `models/guides_folder.py`**

```python
# -*- coding: utf-8 -*-
from odoo import api, fields, models

ACCESS_LEVELS = [('reader', 'Reader'), ('contributor', 'Contributor')]


class GuidesFolder(models.Model):
    _name = 'guides.folder'
    _description = 'Guide Folder'
    _parent_store = True
    _order = 'complete_name'

    name = fields.Char(required=True)
    parent_id = fields.Many2one('guides.folder', string='Parent Folder',
                                ondelete='cascade', index=True)
    parent_path = fields.Char(index=True, unaccent=False)
    complete_name = fields.Char(compute='_compute_complete_name',
                                store=True, recursive=True)
    sequence = fields.Integer(default=10)
    inherit_parent_access = fields.Boolean(
        string='Inherit Parent Access', default=True)
    member_ids = fields.One2many('guides.folder.member', 'folder_id',
                                 string='Members')
    document_ids = fields.One2many('guides.document', 'folder_id',
                                   string='Documents')
    document_count = fields.Integer(compute='_compute_document_count')

    @api.depends('name', 'parent_id.complete_name')
    def _compute_complete_name(self):
        for folder in self:
            if folder.parent_id:
                folder.complete_name = f"{folder.parent_id.complete_name} / {folder.name}"
            else:
                folder.complete_name = folder.name

    def _compute_document_count(self):
        for folder in self:
            folder.document_count = len(folder.document_ids)

    def _get_effective_members(self):
        """Return {user_id(int): 'reader'|'contributor'} for this folder,
        merging ancestor members when inherit_parent_access is set.
        contributor always wins over reader."""
        self.ensure_one()
        result = {}

        def merge(folder):
            for m in folder.member_ids:
                cur = result.get(m.user_id.id)
                if cur != 'contributor':
                    result[m.user_id.id] = m.access_level
            if folder.inherit_parent_access and folder.parent_id:
                merge(folder.parent_id)

        merge(self)
        return result

    def user_can_read(self, user):
        self.ensure_one()
        return user.id in self._get_effective_members()

    def user_can_contribute(self, user):
        self.ensure_one()
        return self._get_effective_members().get(user.id) == 'contributor'


class GuidesFolderMember(models.Model):
    _name = 'guides.folder.member'
    _description = 'Guide Folder Member'

    folder_id = fields.Many2one('guides.folder', required=True,
                                ondelete='cascade')
    user_id = fields.Many2one('res.users', required=True, ondelete='cascade')
    access_level = fields.Selection(ACCESS_LEVELS, required=True,
                                    default='reader')

    _sql_constraints = [
        ('folder_user_uniq', 'unique(folder_id, user_id)',
         'This user is already a member of the folder.'),
    ]
```

- [ ] **Step 4: Register** — add to `models/__init__.py`:

```python
from . import guides_folder
```

- [ ] **Step 5: Add ACL rows** to `ir.model.access.csv`:

```csv
access_guides_folder_user,guides.folder user,model_guides_folder,base.group_user,1,1,1,1
access_guides_folder_member_user,guides.folder.member user,model_guides_folder_member,base.group_user,1,1,1,1
```

- [ ] **Step 6: Run tests to verify they pass** (standard `-u` command). Expected: PASS.

- [ ] **Step 7: Commit**

```bash
git add guides_html_sharing && git commit -m "feat(guides): add folder hierarchy with per-folder ACL members"
```

---

### Task 4: `guides.document` + `guides.document.version` (versioning)

**Files:**
- Create: `guides_html_sharing/models/guides_document.py`
- Create: `guides_html_sharing/models/guides_document_version.py`
- Create: `guides_html_sharing/data/guides_data.xml` (ir.sequence for version numbering is per-document, so use a computed counter instead — no global sequence needed; this file holds the activity type, added in Task 8. Skip creating here.)
- Modify: `models/__init__.py`, `ir.model.access.csv`, `tests/__init__.py`
- Test: `guides_html_sharing/tests/test_document_version.py`

**Interfaces:**
- Produces:
  - `guides.document` (inherits `mail.thread`, `mail.activity.mixin`): fields `name` (Char req), `folder_id` (Many2one req), `owner_id` (Many2one res.users, default create_uid), `editor_ids` (Many2many res.users), `tag_ids` (Many2many guides.tag), `project_id` (Many2one project.project), `task_id` (Many2one project.task), `version_ids` (One2many), `active_version_id` (Many2one guides.document.version), `version_count` (Integer computed), `content_html` (Text related `active_version_id.content_html`, readonly), `active` (Boolean default True), `share_token`/`share_active`/`share_expiry` (added Task 6).
  - Methods: `action_add_version(content_html, source='inline', original_filename=False, changelog=False)` → creates version, returns it; `action_restore_version(version)` → creates new version copying `version.content_html`.
  - `_onchange_task_id` sets `project_id`.
  - `guides.document.version`: `document_id` (Many2one req), `version_number` (Integer), `content_html` (Text), `source` (Selection upload/inline), `original_filename` (Char), `changelog` (Char).

- [ ] **Step 1: Write the failing test** — add `from . import test_document_version` to `tests/__init__.py`; `tests/test_document_version.py`:

```python
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
```

- [ ] **Step 2: Run test to verify it fails** (standard `-u` command). Expected: FAIL — `guides.document` not found.

- [ ] **Step 3: Create `models/guides_document_version.py`**

```python
# -*- coding: utf-8 -*-
from odoo import fields, models

VERSION_SOURCES = [('inline', 'Inline Edit'), ('upload', 'File Upload')]


class GuidesDocumentVersion(models.Model):
    _name = 'guides.document.version'
    _description = 'Guide Document Version'
    _order = 'version_number desc'

    document_id = fields.Many2one('guides.document', required=True,
                                  ondelete='cascade', index=True)
    version_number = fields.Integer(string='Version', default=1)
    content_html = fields.Text(string='HTML Content')
    source = fields.Selection(VERSION_SOURCES, default='inline')
    original_filename = fields.Char()
    changelog = fields.Char()

    def name_get(self):
        return [(v.id, f"v{v.version_number}") for v in self]
```

- [ ] **Step 4: Create `models/guides_document.py`**

```python
# -*- coding: utf-8 -*-
from odoo import api, fields, models


class GuidesDocument(models.Model):
    _name = 'guides.document'
    _description = 'Guide Document'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'name'

    name = fields.Char(required=True, tracking=True)
    active = fields.Boolean(default=True)
    folder_id = fields.Many2one('guides.folder', string='Folder',
                                required=True, tracking=True, index=True)
    owner_id = fields.Many2one('res.users', string='Owner',
                               default=lambda self: self.env.user,
                               tracking=True, index=True)
    editor_ids = fields.Many2many('res.users', 'guides_document_editor_rel',
                                  'document_id', 'user_id', string='Editors')
    tag_ids = fields.Many2many('guides.tag', string='Tags')
    project_id = fields.Many2one('project.project', string='Project')
    task_id = fields.Many2one('project.task', string='Task')

    version_ids = fields.One2many('guides.document.version', 'document_id',
                                  string='Versions')
    active_version_id = fields.Many2one('guides.document.version',
                                        string='Current Version')
    version_count = fields.Integer(compute='_compute_version_count')
    content_html = fields.Text(related='active_version_id.content_html',
                               string='Current HTML', readonly=True)

    @api.depends('version_ids')
    def _compute_version_count(self):
        for doc in self:
            doc.version_count = len(doc.version_ids)

    @api.onchange('task_id')
    def _onchange_task_id(self):
        if self.task_id:
            self.project_id = self.task_id.project_id

    @api.model_create_multi
    def create(self, vals_list):
        docs = super().create(vals_list)
        for doc in docs:
            # Number any versions created inline, and set the latest active.
            versions = doc.version_ids.sorted('id')
            for idx, v in enumerate(versions, start=1):
                v.version_number = idx
            if versions and not doc.active_version_id:
                doc.active_version_id = versions[-1]
        return docs

    def _next_version_number(self):
        self.ensure_one()
        return max(self.version_ids.mapped('version_number') or [0]) + 1

    def action_add_version(self, content_html, source='inline',
                           original_filename=False, changelog=False):
        self.ensure_one()
        version = self.env['guides.document.version'].create({
            'document_id': self.id,
            'version_number': self._next_version_number(),
            'content_html': content_html,
            'source': source,
            'original_filename': original_filename,
            'changelog': changelog,
        })
        self.active_version_id = version
        self.message_post(body=f"New version v{version.version_number} added.")
        return version

    def action_restore_version(self, version):
        self.ensure_one()
        return self.action_add_version(
            version.content_html, source=version.source,
            changelog=f"Restored from v{version.version_number}")
```

- [ ] **Step 5: Register** — add to `models/__init__.py`:

```python
from . import guides_document_version
from . import guides_document
```

- [ ] **Step 6: Add ACL rows** to `ir.model.access.csv`:

```csv
access_guides_document_user,guides.document user,model_guides_document,base.group_user,1,1,1,1
access_guides_document_version_user,guides.document.version user,model_guides_document_version,base.group_user,1,1,1,1
```

- [ ] **Step 7: Run tests to verify they pass** (standard `-u`). Expected: PASS.

- [ ] **Step 8: Commit**

```bash
git add guides_html_sharing && git commit -m "feat(guides): add document + immutable version model with versioning"
```

---

### Task 5: Security groups + record rules + folder-based create gating

**Files:**
- Create: `guides_html_sharing/security/guides_security.xml`
- Modify: `guides_html_sharing/security/ir.model.access.csv` (split per group)
- Modify: `guides_html_sharing/models/guides_document.py` (create gating + read/write helpers)
- Modify: `__manifest__.py` (add `security/guides_security.xml` BEFORE the csv in `data`)
- Modify: `tests/__init__.py`
- Test: `guides_html_sharing/tests/test_permissions.py`

**Interfaces:**
- Produces: groups `group_guides_viewer`, `group_guides_user`, `group_guides_admin` (XML ids in `guides_html_sharing`). Document `create()` raises `AccessError` when a non-admin user lacks contributor rights on `folder_id`.

- [ ] **Step 1: Write the failing test** — add `from . import test_permissions`; `tests/test_permissions.py`:

```python
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
        cls.contrib = cls.env['res.users'].create({
            'name': 'Contrib', 'login': 'contrib_g', 'email': 'c@x.com',
            'groups_id': [(6, 0, [g_user.id])]})
        cls.viewer = cls.env['res.users'].create({
            'name': 'Viewer', 'login': 'viewer_g', 'email': 'v@x.com',
            'groups_id': [(6, 0, [g_view.id])]})
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
        # viewer not a follower -> cannot read
        with self.assertRaises(AccessError):
            doc.with_user(self.viewer).read(['name'])
        # add as follower -> can read
        doc.message_subscribe(partner_ids=[self.viewer.partner_id.id])
        self.assertEqual(
            doc.with_user(self.viewer).read(['name'])[0]['name'], 'Secret')
```

- [ ] **Step 2: Run test to verify it fails** (standard `-u`). Expected: FAIL — group refs missing.

- [ ] **Step 3: Create `security/guides_security.xml`**

```xml
<?xml version="1.0" encoding="utf-8"?>
<odoo>
    <record id="module_category_guides" model="ir.module.category">
        <field name="name">Guides</field>
        <field name="sequence">20</field>
    </record>

    <record id="group_guides_viewer" model="res.groups">
        <field name="name">Viewer</field>
        <field name="category_id" ref="module_category_guides"/>
    </record>
    <record id="group_guides_user" model="res.groups">
        <field name="name">User</field>
        <field name="category_id" ref="module_category_guides"/>
        <field name="implied_ids" eval="[(4, ref('group_guides_viewer'))]"/>
    </record>
    <record id="group_guides_admin" model="res.groups">
        <field name="name">Administrator</field>
        <field name="category_id" ref="module_category_guides"/>
        <field name="implied_ids" eval="[(4, ref('group_guides_user'))]"/>
        <field name="users" eval="[(4, ref('base.user_admin'))]"/>
    </record>

    <!-- Admin: full access to all documents -->
    <record id="rule_document_admin" model="ir.rule">
        <field name="name">Guide Document: admin full access</field>
        <field name="model_id" ref="model_guides_document"/>
        <field name="groups" eval="[(4, ref('group_guides_admin'))]"/>
        <field name="domain_force">[(1, '=', 1)]</field>
        <field name="perm_read" eval="True"/>
        <field name="perm_write" eval="True"/>
        <field name="perm_create" eval="True"/>
        <field name="perm_unlink" eval="True"/>
    </record>

    <!-- Non-admin READ: follower OR owner OR editor OR folder member -->
    <record id="rule_document_read" model="ir.rule">
        <field name="name">Guide Document: read scope</field>
        <field name="model_id" ref="model_guides_document"/>
        <field name="groups" eval="[(4, ref('group_guides_viewer'))]"/>
        <field name="perm_read" eval="True"/>
        <field name="perm_write" eval="False"/>
        <field name="perm_create" eval="False"/>
        <field name="perm_unlink" eval="False"/>
        <field name="domain_force">['|', '|', '|',
            ('message_partner_ids', 'in', [user.partner_id.id]),
            ('owner_id', '=', user.id),
            ('editor_ids', 'in', [user.id]),
            ('folder_id.member_ids.user_id', 'in', [user.id])]</field>
    </record>

    <!-- Non-admin WRITE/UNLINK: owner OR editor -->
    <record id="rule_document_write" model="ir.rule">
        <field name="name">Guide Document: write scope</field>
        <field name="model_id" ref="model_guides_document"/>
        <field name="groups" eval="[(4, ref('group_guides_user'))]"/>
        <field name="perm_read" eval="False"/>
        <field name="perm_write" eval="True"/>
        <field name="perm_create" eval="True"/>
        <field name="perm_unlink" eval="True"/>
        <field name="domain_force">['|',
            ('owner_id', '=', user.id),
            ('editor_ids', 'in', [user.id])]</field>
    </record>
</odoo>
```

> NOTE: the folder-member read clause uses `folder_id.member_ids.user_id` which
> only matches direct membership. Inherited (ancestor) access is enforced in
> Python helpers and the controller; the record rule grants direct-folder reads,
> which is the common case. Document this limitation in the commit message.

- [ ] **Step 4: Rewrite `ir.model.access.csv`** with per-group rows (base CRUD; rows narrowed by rules):

```csv
id,name,model_id:id,group_id:id,perm_read,perm_write,perm_create,perm_unlink
access_guides_tag_viewer,guides.tag viewer,model_guides_tag,guides_html_sharing.group_guides_viewer,1,0,0,0
access_guides_tag_user,guides.tag user,model_guides_tag,guides_html_sharing.group_guides_user,1,1,1,0
access_guides_tag_admin,guides.tag admin,model_guides_tag,guides_html_sharing.group_guides_admin,1,1,1,1
access_guides_folder_viewer,guides.folder viewer,model_guides_folder,guides_html_sharing.group_guides_viewer,1,0,0,0
access_guides_folder_user,guides.folder user,model_guides_folder,guides_html_sharing.group_guides_user,1,0,0,0
access_guides_folder_admin,guides.folder admin,model_guides_folder,guides_html_sharing.group_guides_admin,1,1,1,1
access_guides_folder_member_viewer,guides.folder.member viewer,model_guides_folder_member,guides_html_sharing.group_guides_viewer,1,0,0,0
access_guides_folder_member_user,guides.folder.member user,model_guides_folder_member,guides_html_sharing.group_guides_user,1,0,0,0
access_guides_folder_member_admin,guides.folder.member admin,model_guides_folder_member,guides_html_sharing.group_guides_admin,1,1,1,1
access_guides_document_viewer,guides.document viewer,model_guides_document,guides_html_sharing.group_guides_viewer,1,0,0,0
access_guides_document_user,guides.document user,model_guides_document,guides_html_sharing.group_guides_user,1,1,1,1
access_guides_document_admin,guides.document admin,model_guides_document,guides_html_sharing.group_guides_admin,1,1,1,1
access_guides_version_viewer,guides.document.version viewer,model_guides_document_version,guides_html_sharing.group_guides_viewer,1,0,0,0
access_guides_version_user,guides.document.version user,model_guides_document_version,guides_html_sharing.group_guides_user,1,1,1,1
access_guides_version_admin,guides.document.version admin,model_guides_document_version,guides_html_sharing.group_guides_admin,1,1,1,1
```

- [ ] **Step 5: Add create gating** in `models/guides_document.py` — extend `create()` (add at the start of the method body, before `super()`):

```python
    @api.model_create_multi
    def create(self, vals_list):
        if not self.env.is_superuser() and not self.env.user.has_group(
                'guides_html_sharing.group_guides_admin'):
            for vals in vals_list:
                folder = self.env['guides.folder'].browse(vals.get('folder_id'))
                if folder and not folder.sudo().user_can_contribute(self.env.user):
                    raise self.env['ir.exceptions'].AccessError if False else \
                        __import__('odoo').exceptions.AccessError(
                            "You don't have contributor rights on this folder.")
        docs = super().create(vals_list)
        ...
```

> CLEANER form — put `from odoo.exceptions import AccessError` at the top of the
> file and write the check as:
> ```python
>     @api.model_create_multi
>     def create(self, vals_list):
>         is_admin = self.env.is_superuser() or self.env.user.has_group(
>             'guides_html_sharing.group_guides_admin')
>         if not is_admin:
>             for vals in vals_list:
>                 folder = self.env['guides.folder'].browse(vals.get('folder_id'))
>                 if not folder or not folder.sudo().user_can_contribute(self.env.user):
>                     raise AccessError(
>                         "You don't have contributor rights on this folder.")
>         docs = super().create(vals_list)
>         for doc in docs:
>             versions = doc.version_ids.sorted('id')
>             for idx, v in enumerate(versions, start=1):
>                 v.version_number = idx
>             if versions and not doc.active_version_id:
>                 doc.active_version_id = versions[-1]
>         return docs
> ```
> Replace the whole `create` method from Task 4 with this version. Add the import.

- [ ] **Step 6: Update `__manifest__.py`** `data` list to include security first:

```python
    'data': [
        'security/guides_security.xml',
        'security/ir.model.access.csv',
    ],
```

- [ ] **Step 7: Run tests to verify they pass** (standard `-u`). Expected: PASS.

- [ ] **Step 8: Commit**

```bash
git add guides_html_sharing && git commit -m "feat(guides): add roles, record rules, and folder-based create gating"
```

---

### Task 6: Share token (generate / revoke / expiry)

**Files:**
- Modify: `guides_html_sharing/models/guides_document.py`
- Modify: `tests/__init__.py`
- Test: `guides_html_sharing/tests/test_share_token.py`

**Interfaces:**
- Produces on `guides.document`: fields `share_token` (Char, copy=False, index), `share_active` (Boolean), `share_expiry` (Datetime). Methods `action_enable_share()` (sets token if missing + share_active True; returns full URL via `get_base_url()`), `action_revoke_share()` (share_active=False), `action_regenerate_token()`, `_is_share_valid()` (bool: active and not expired). Class method `_get_valid_shared_document(token)` → document or empty recordset (sudo).

- [ ] **Step 1: Write the failing test** — add `from . import test_share_token`; `tests/test_share_token.py`:

```python
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
```

- [ ] **Step 2: Run test to verify it fails** (standard `-u`). Expected: FAIL — no `share_token`.

- [ ] **Step 3: Implement** — in `models/guides_document.py` add import and fields/methods:

```python
import secrets
from odoo import fields  # already imported; ensure present
```

Add fields (near the others):

```python
    share_token = fields.Char(copy=False, index=True, readonly=True)
    share_active = fields.Boolean(string='Public Link Enabled', default=False)
    share_expiry = fields.Datetime(string='Link Expiry')
```

Add methods:

```python
    def action_enable_share(self):
        self.ensure_one()
        if not self.share_token:
            self.share_token = secrets.token_urlsafe(24)
        self.share_active = True
        return f"{self.get_base_url()}/guides/public/{self.share_token}"

    def action_regenerate_token(self):
        self.ensure_one()
        self.share_token = secrets.token_urlsafe(24)
        return self.action_enable_share()

    def action_revoke_share(self):
        self.share_active = False

    def _is_share_valid(self):
        self.ensure_one()
        if not self.share_active or not self.share_token:
            return False
        if self.share_expiry and self.share_expiry < fields.Datetime.now():
            return False
        return True

    @api.model
    def _get_valid_shared_document(self, token):
        if not token:
            return self.browse()
        doc = self.sudo().search([('share_token', '=', token)], limit=1)
        return doc if (doc and doc._is_share_valid()) else self.browse()
```

- [ ] **Step 4: Run tests to verify they pass** (standard `-u`). Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add guides_html_sharing && git commit -m "feat(guides): add revocable public share token with expiry"
```

---

### Task 7: `project.task` / `project.project` integration

**Files:**
- Create: `guides_html_sharing/models/project_task.py`
- Modify: `models/__init__.py`, `tests/__init__.py`
- Test: `guides_html_sharing/tests/test_project.py`

**Interfaces:**
- Produces: `project.task` gains `guide_document_ids` (One2many `guides.document`, inverse `task_id`) and `guide_document_count` (Integer computed) + `action_view_guides()` returning an act_window dict filtered to the task. Same pattern on `project.project` (inverse `project_id`).

- [ ] **Step 1: Write the failing test** — add `from . import test_project`; `tests/test_project.py`:

```python
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
```

- [ ] **Step 2: Run test to verify it fails** (standard `-u`). Expected: FAIL.

- [ ] **Step 3: Create `models/project_task.py`**

```python
# -*- coding: utf-8 -*-
from odoo import fields, models


class ProjectTask(models.Model):
    _inherit = 'project.task'

    guide_document_ids = fields.One2many('guides.document', 'task_id',
                                         string='Guides')
    guide_document_count = fields.Integer(compute='_compute_guide_count')

    def _compute_guide_count(self):
        for task in self:
            task.guide_document_count = len(task.guide_document_ids)

    def action_view_guides(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Guides',
            'res_model': 'guides.document',
            'view_mode': 'kanban,list,form',
            'domain': [('task_id', '=', self.id)],
            'context': {'default_task_id': self.id,
                        'default_project_id': self.project_id.id},
        }


class ProjectProject(models.Model):
    _inherit = 'project.project'

    guide_document_ids = fields.One2many('guides.document', 'project_id',
                                         string='Guides')
    guide_document_count = fields.Integer(compute='_compute_guide_count')

    def _compute_guide_count(self):
        for project in self:
            project.guide_document_count = len(project.guide_document_ids)

    def action_view_guides(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Guides',
            'res_model': 'guides.document',
            'view_mode': 'kanban,list,form',
            'domain': [('project_id', '=', self.id)],
            'context': {'default_project_id': self.id},
        }
```

- [ ] **Step 4: Register** — add `from . import project_task` to `models/__init__.py`.

- [ ] **Step 5: Run tests to verify they pass** (standard `-u`). Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add guides_html_sharing && git commit -m "feat(guides): link documents to project tasks and projects"
```

---

### Task 8: Access-request flow + activity

**Files:**
- Create: `guides_html_sharing/models/guides_access_request.py`
- Create: `guides_html_sharing/data/guides_data.xml` (activity type)
- Modify: `guides_html_sharing/models/guides_document.py` (request/approve methods)
- Modify: `models/__init__.py`, `ir.model.access.csv`, `__manifest__.py` (add data file), `tests/__init__.py`
- Test: `guides_html_sharing/tests/test_access_request.py`

**Interfaces:**
- Produces:
  - `guides.access.request`: `document_id` (Many2one req), `user_id` (Many2one res.users, default current user), `state` (Selection pending/approved/rejected, default pending), `note` (Text). Methods `action_approve()` (adds `user_id` to `document_id.editor_ids`, state=approved, marks linked activity done, notifies), `action_reject()`.
  - `guides.document.action_request_edit_access(note=False)` → creates the request and schedules a `mail.activity` (type `guides_html_sharing.mail_activity_edit_request`) for `owner_id`; returns the request.

- [ ] **Step 1: Write the failing test** — add `from . import test_access_request`; `tests/test_access_request.py`:

```python
# -*- coding: utf-8 -*-
from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install', 'guides_html_sharing')
class TestAccessRequest(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        g_user = cls.env.ref('guides_html_sharing.group_guides_user')
        cls.owner = cls.env['res.users'].create({
            'name': 'Owner', 'login': 'owner_g', 'email': 'o@x.com',
            'groups_id': [(6, 0, [g_user.id])]})
        cls.req_user = cls.env['res.users'].create({
            'name': 'Req', 'login': 'req_g', 'email': 'r@x.com',
            'groups_id': [(6, 0, [g_user.id])]})
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
```

- [ ] **Step 2: Run test to verify it fails** (standard `-u`). Expected: FAIL.

- [ ] **Step 3: Create `data/guides_data.xml`**

```xml
<?xml version="1.0" encoding="utf-8"?>
<odoo noupdate="1">
    <record id="mail_activity_edit_request" model="mail.activity.type">
        <field name="name">Guide Edit Access Request</field>
        <field name="icon">fa-pencil</field>
        <field name="res_model">guides.document</field>
    </record>
</odoo>
```

- [ ] **Step 4: Create `models/guides_access_request.py`**

```python
# -*- coding: utf-8 -*-
from odoo import api, fields, models

REQUEST_STATES = [('pending', 'Pending'), ('approved', 'Approved'),
                  ('rejected', 'Rejected')]


class GuidesAccessRequest(models.Model):
    _name = 'guides.access.request'
    _description = 'Guide Edit Access Request'
    _order = 'create_date desc'

    document_id = fields.Many2one('guides.document', required=True,
                                  ondelete='cascade')
    user_id = fields.Many2one('res.users', required=True,
                              default=lambda self: self.env.user)
    state = fields.Selection(REQUEST_STATES, default='pending', required=True)
    note = fields.Text()

    def action_approve(self):
        for req in self:
            req.document_id.sudo().write(
                {'editor_ids': [(4, req.user_id.id)]})
            req.state = 'approved'
            req.document_id.activity_ids.filtered(
                lambda a: a.activity_type_id == self.env.ref(
                    'guides_html_sharing.mail_activity_edit_request')
            ).action_done()
            req.document_id.message_post(
                body=f"Edit access granted to {req.user_id.name}.",
                partner_ids=[req.user_id.partner_id.id])

    def action_reject(self):
        self.write({'state': 'rejected'})
```

- [ ] **Step 5: Add to `guides_document.py`**

```python
    def action_request_edit_access(self, note=False):
        self.ensure_one()
        request = self.env['guides.access.request'].create({
            'document_id': self.id,
            'user_id': self.env.user.id,
            'note': note,
        })
        self.activity_schedule(
            'guides_html_sharing.mail_activity_edit_request',
            user_id=self.owner_id.id,
            note=f"{self.env.user.name} requested edit access. {note or ''}",
            summary='Edit access requested')
        return request
```

- [ ] **Step 6: Register + ACL + manifest**

`models/__init__.py`: add `from . import guides_access_request`.

`ir.model.access.csv` add:

```csv
access_guides_access_request_user,guides.access.request user,model_guides_access_request,guides_html_sharing.group_guides_user,1,1,1,0
access_guides_access_request_admin,guides.access.request admin,model_guides_access_request,guides_html_sharing.group_guides_admin,1,1,1,1
```

`__manifest__.py` `data`: insert `'data/guides_data.xml',` after the csv.

- [ ] **Step 7: Run tests to verify they pass** (standard `-u`). Expected: PASS.

- [ ] **Step 8: Commit**

```bash
git add guides_html_sharing && git commit -m "feat(guides): edit-access request flow with owner activity"
```

---

### Task 9: HTTP controllers (backend render + public token)

**Files:**
- Create: `guides_html_sharing/controllers/__init__.py`
- Create: `guides_html_sharing/controllers/main.py`
- Modify: `guides_html_sharing/__init__.py` (import controllers)
- Modify: `tests/__init__.py`
- Test: `guides_html_sharing/tests/test_controllers.py` (uses `HttpCase`)

**Interfaces:**
- Produces routes:
  - `GET /guides/render/<int:document_id>` and `/guides/render/<int:document_id>/v/<int:version_id>` (`auth='user'`): returns the version HTML with CSP header `frame-ancestors 'self'`. Returns 404 if no access/record.
  - `GET /guides/public/<string:token>` (`auth='public'`, `csrf=False`): returns active-version HTML for a valid token, else a 404 page.
- Consumes: `guides.document._get_valid_shared_document`, `active_version_id.content_html`.

- [ ] **Step 1: Write the failing test** — add `from . import test_controllers`; `tests/test_controllers.py`:

```python
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
        self.env.cr.commit()
        self.addCleanup(doc.unlink)
        res = self.url_open(f"/guides/public/{doc.share_token}")
        self.assertEqual(res.status_code, 200)
        self.assertIn('PUBLIC', res.text)

    def test_public_route_bad_token(self):
        res = self.url_open("/guides/public/nope-not-real")
        self.assertEqual(res.status_code, 404)
```

> NOTE: `HttpCase` runs against the live cursor; the `env.cr.commit()` +
> `addCleanup(unlink)` pattern makes the record visible to the HTTP worker.

- [ ] **Step 2: Run test to verify it fails** (standard `-u`, but drop `--no-http` so HttpCase works):

```bash
docker compose exec -T odoo odoo -d postgres -u guides_html_sharing \
  --test-enable --test-tags /guides_html_sharing --stop-after-init 2>&1 | tail -40
```

Expected: FAIL — route 404 (controller missing).

- [ ] **Step 3: Create `controllers/__init__.py`**

```python
# -*- coding: utf-8 -*-
from . import main
```

- [ ] **Step 4: Create `controllers/main.py`**

```python
# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request


def _html_response(html, embeddable_self=True):
    html = html or "<!DOCTYPE html><html><body><p>No content.</p></body></html>"
    headers = [
        ('Content-Type', 'text/html; charset=utf-8'),
        ('Content-Security-Policy', "frame-ancestors 'self'"),
    ]
    return request.make_response(html, headers=headers)


class GuidesController(http.Controller):

    @http.route(['/guides/render/<int:document_id>',
                 '/guides/render/<int:document_id>/v/<int:version_id>'],
                type='http', auth='user', methods=['GET'])
    def render_document(self, document_id, version_id=None, **kw):
        doc = request.env['guides.document'].browse(document_id)
        if not doc.exists() or not doc.has_access('read'):
            return request.not_found()
        version = doc.active_version_id
        if version_id:
            candidate = request.env['guides.document.version'].browse(version_id)
            if candidate.exists() and candidate.document_id == doc:
                version = candidate
        return _html_response(version.content_html)

    @http.route('/guides/public/<string:token>', type='http',
                auth='public', methods=['GET'], csrf=False, sitemap=False)
    def render_public(self, token, **kw):
        doc = request.env['guides.document'].sudo()._get_valid_shared_document(token)
        if not doc:
            return request.not_found()
        return _html_response(doc.active_version_id.content_html)
```

> `has_access('read')` is the Odoo 19 record access check; if unavailable on this
> build, fall back to wrapping `doc.check_access('read')` in try/except returning
> `request.not_found()` on `AccessError`.

- [ ] **Step 5: Import controllers** — `__init__.py`:

```python
# -*- coding: utf-8 -*-
from . import models
from . import controllers
```

- [ ] **Step 6: Run tests to verify they pass** (command from Step 2, no `--no-http`). Expected: PASS.

- [ ] **Step 7: Commit**

```bash
git add guides_html_sharing && git commit -m "feat(guides): backend render + tokenized public HTML controllers"
```

---

### Task 10: Backend views + menus

**Files:**
- Create: `guides_html_sharing/views/guides_tag_views.xml`
- Create: `guides_html_sharing/views/guides_folder_views.xml`
- Create: `guides_html_sharing/views/guides_document_views.xml`
- Create: `guides_html_sharing/views/project_task_views.xml`
- Create: `guides_html_sharing/views/guides_menus.xml`
- Modify: `__manifest__.py` (`data`: add the five view files in order)

**Interfaces:**
- Produces: act_window actions `action_guides_document`, `action_guides_folder`, `action_guides_tag`; root menu `menu_guides_root` (application) with children. Document form embeds the render iframe and exposes share/version/request buttons. Project task form gets a "Guides" smart button.

> This task has no unit test (declarative views). Verification = clean install +
> manual UI smoke. Keep each `<record>`/`<menuitem>` minimal and valid.

- [ ] **Step 1: Create `views/guides_tag_views.xml`**

```xml
<?xml version="1.0" encoding="utf-8"?>
<odoo>
    <record id="view_guides_tag_list" model="ir.ui.view">
        <field name="name">guides.tag.list</field>
        <field name="model">guides.tag</field>
        <field name="arch" type="xml">
            <list editable="bottom">
                <field name="name"/>
                <field name="color" widget="color_picker"/>
            </list>
        </field>
    </record>
    <record id="action_guides_tag" model="ir.actions.act_window">
        <field name="name">Tags</field>
        <field name="res_model">guides.tag</field>
        <field name="view_mode">list</field>
    </record>
</odoo>
```

- [ ] **Step 2: Create `views/guides_folder_views.xml`**

```xml
<?xml version="1.0" encoding="utf-8"?>
<odoo>
    <record id="view_guides_folder_form" model="ir.ui.view">
        <field name="name">guides.folder.form</field>
        <field name="model">guides.folder</field>
        <field name="arch" type="xml">
            <form>
                <sheet>
                    <group>
                        <field name="name"/>
                        <field name="parent_id"/>
                        <field name="inherit_parent_access"/>
                        <field name="complete_name" readonly="1"/>
                    </group>
                    <notebook>
                        <page string="Members">
                            <field name="member_ids">
                                <list editable="bottom">
                                    <field name="user_id"/>
                                    <field name="access_level"/>
                                </list>
                            </field>
                        </page>
                    </notebook>
                </sheet>
            </form>
        </field>
    </record>
    <record id="view_guides_folder_list" model="ir.ui.view">
        <field name="name">guides.folder.list</field>
        <field name="model">guides.folder</field>
        <field name="arch" type="xml">
            <list>
                <field name="complete_name"/>
                <field name="document_count"/>
            </list>
        </field>
    </record>
    <record id="action_guides_folder" model="ir.actions.act_window">
        <field name="name">Folders</field>
        <field name="res_model">guides.folder</field>
        <field name="view_mode">list,form</field>
    </record>
</odoo>
```

- [ ] **Step 3: Create `views/guides_document_views.xml`**

```xml
<?xml version="1.0" encoding="utf-8"?>
<odoo>
    <record id="view_guides_document_form" model="ir.ui.view">
        <field name="name">guides.document.form</field>
        <field name="model">guides.document</field>
        <field name="arch" type="xml">
            <form>
                <header>
                    <button name="action_enable_share" type="object"
                            string="Enable Public Link" class="btn-primary"/>
                    <button name="action_revoke_share" type="object"
                            string="Revoke Link"
                            invisible="not share_active"/>
                    <button name="action_request_edit_access" type="object"
                            string="Request Edit Access"/>
                </header>
                <sheet>
                    <div class="oe_button_box" name="button_box">
                        <button class="oe_stat_button" icon="fa-history"
                                type="object" name="toggle_active" disabled="1">
                            <field name="version_count" widget="statinfo"
                                   string="Versions"/>
                        </button>
                    </div>
                    <group>
                        <group>
                            <field name="name"/>
                            <field name="folder_id"/>
                            <field name="owner_id"/>
                            <field name="tag_ids" widget="many2many_tags"
                                   options="{'color_field': 'color'}"/>
                        </group>
                        <group>
                            <field name="project_id"/>
                            <field name="task_id"/>
                            <field name="editor_ids" widget="many2many_tags"/>
                            <field name="share_active"/>
                            <field name="share_expiry"
                                   invisible="not share_active"/>
                            <field name="share_token" readonly="1"
                                   invisible="not share_active"/>
                        </group>
                    </group>
                    <notebook>
                        <page string="Preview">
                            <field name="active_version_id" invisible="1"/>
                            <iframe t-if="record.id"
                                    t-att-src="'/guides/render/' + record.resId"
                                    sandbox="allow-scripts"
                                    style="width:100%;height:600px;border:1px solid #ddd;"/>
                        </page>
                        <page string="Versions">
                            <field name="version_ids">
                                <list>
                                    <field name="version_number"/>
                                    <field name="source"/>
                                    <field name="original_filename"/>
                                    <field name="create_uid"/>
                                    <field name="create_date"/>
                                    <field name="changelog"/>
                                </list>
                            </field>
                        </page>
                    </notebook>
                </sheet>
                <chatter/>
            </form>
        </field>
    </record>

    <record id="view_guides_document_kanban" model="ir.ui.view">
        <field name="name">guides.document.kanban</field>
        <field name="model">guides.document</field>
        <field name="arch" type="xml">
            <kanban>
                <field name="folder_id"/>
                <field name="tag_ids"/>
                <templates>
                    <t t-name="card">
                        <div class="oe_kanban_global_click p-2">
                            <strong><field name="name"/></strong>
                            <div class="text-muted"><field name="folder_id"/></div>
                            <field name="tag_ids" widget="many2many_tags"/>
                        </div>
                    </t>
                </templates>
            </kanban>
        </field>
    </record>

    <record id="view_guides_document_list" model="ir.ui.view">
        <field name="name">guides.document.list</field>
        <field name="model">guides.document</field>
        <field name="arch" type="xml">
            <list>
                <field name="name"/>
                <field name="folder_id"/>
                <field name="owner_id"/>
                <field name="version_count"/>
                <field name="share_active"/>
            </list>
        </field>
    </record>

    <record id="action_guides_document" model="ir.actions.act_window">
        <field name="name">Documents</field>
        <field name="res_model">guides.document</field>
        <field name="view_mode">kanban,list,form</field>
    </record>
</odoo>
```

> NOTE on the `<iframe>`: embedding via `t-att-src` requires the view to render
> the field context. If the inline iframe proves finicky in the form renderer,
> fall back to a button `Open Preview` that does `window.open('/guides/render/'+id)`.
> The authoritative viewer is the OWL browser (Task 11); this form preview is a
> convenience. Keep the form installable above all.

- [ ] **Step 4: Create `views/project_task_views.xml`**

```xml
<?xml version="1.0" encoding="utf-8"?>
<odoo>
    <record id="view_task_form_guides" model="ir.ui.view">
        <field name="name">project.task.form.guides</field>
        <field name="model">project.task</field>
        <field name="inherit_id" ref="project.view_task_form2"/>
        <field name="arch" type="xml">
            <xpath expr="//div[@name='button_box']" position="inside">
                <button class="oe_stat_button" icon="fa-book"
                        type="object" name="action_view_guides">
                    <field name="guide_document_count" widget="statinfo"
                           string="Guides"/>
                </button>
            </xpath>
        </field>
    </record>
</odoo>
```

> If `project.view_task_form2` is not the correct external id on this Odoo 19
> build, find the task form id with:
> `docker compose exec -T odoo odoo shell -d postgres` →
> `self.env.ref('project.view_task_form2')`, or grep enterprise/community
> `project` views. Adjust the `inherit_id`.

- [ ] **Step 5: Create `views/guides_menus.xml`**

```xml
<?xml version="1.0" encoding="utf-8"?>
<odoo>
    <menuitem id="menu_guides_root" name="Guides"
              web_icon="guides_html_sharing,static/description/icon.png"
              sequence="50"/>
    <menuitem id="menu_guides_documents" name="Documents"
              parent="menu_guides_root" action="action_guides_document"
              sequence="10"/>
    <menuitem id="menu_guides_folders" name="Folders"
              parent="menu_guides_root" action="action_guides_folder"
              sequence="20" groups="guides_html_sharing.group_guides_user"/>
    <menuitem id="menu_guides_tags" name="Tags"
              parent="menu_guides_root" action="action_guides_tag"
              sequence="30" groups="guides_html_sharing.group_guides_user"/>
</odoo>
```

> The OWL browser menu (client action) is added in Task 11. `web_icon` references
> an icon added in Task 11 Step 0; until then, drop the `web_icon` attribute to
> keep the menu installable.

- [ ] **Step 6: Update `__manifest__.py`** `data` to final order:

```python
    'data': [
        'security/guides_security.xml',
        'security/ir.model.access.csv',
        'data/guides_data.xml',
        'views/guides_tag_views.xml',
        'views/guides_folder_views.xml',
        'views/guides_document_views.xml',
        'views/project_task_views.xml',
        'views/guides_menus.xml',
    ],
```

- [ ] **Step 7: Install + run full suite** (no `--no-http`):

```bash
docker compose exec -T odoo odoo -d postgres -u guides_html_sharing \
  --test-enable --test-tags /guides_html_sharing --stop-after-init 2>&1 | tail -40
```

Expected: module updates clean (no XML/view errors), tests `0 failed, 0 error(s)`.

- [ ] **Step 8: Manual smoke** — log into the web UI, open the **Guides** app, create a folder, create a document with an inline version, confirm the Preview iframe renders and the task smart button appears on a task linked via `task_id`.

- [ ] **Step 9: Commit**

```bash
git add guides_html_sharing && git commit -m "feat(guides): backend views, menus, and task smart button"
```

---

### Task 11: OWL document browser (client action)

**Files:**
- Create: `guides_html_sharing/static/src/guides_browser/guides_browser.js`
- Create: `guides_html_sharing/static/src/guides_browser/guides_browser.xml`
- Create: `guides_html_sharing/static/src/guides_browser/guides_browser.scss`
- Create: `guides_html_sharing/static/description/icon.png` (any 140x140 PNG placeholder)
- Modify: `views/guides_menus.xml` (add client action + menu entry; restore `web_icon`)
- Modify: `__manifest__.py` (`assets` already lists the three static files from Task 1)

**Interfaces:**
- Produces: client action tag `guides_browser` (registry `actions`) rendering a left folder/document tree and a right iframe pane that loads `/guides/render/<doc_id>`; reads data via `orm.searchRead` on `guides.folder` and `guides.document`.

> No unit test (OWL UI). Verification = manual smoke in Step 6.

- [ ] **Step 1: Add icon** — create a 140x140 placeholder PNG:

```bash
cd /home/krasorx/server/odoo-19-ee/addons/odoo-dashboards/guides_html_sharing
mkdir -p static/description
docker compose -f /home/krasorx/server/odoo-19-ee/docker-compose.yml exec -T odoo \
  python3 -c "import base64,sys; open('/dev/stdout','wb').write(base64.b64decode('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYAAAAAYAAjCB0C8AAAAASUVORK5CYII='))" > static/description/icon.png || true
```

> Any valid PNG works; if the above is awkward, copy an existing icon:
> `cp ../kpi_widgets/static/description/icon.png static/description/icon.png`
> (check it exists first; otherwise commit a 1x1 PNG).

- [ ] **Step 2: Create `static/src/guides_browser/guides_browser.js`**

```javascript
/** @odoo-module */
import { Component, useState, onWillStart } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";

export class GuidesBrowser extends Component {
    static template = "guides_html_sharing.GuidesBrowser";
    static props = ["*"];

    setup() {
        this.orm = useService("orm");
        this.state = useState({
            folders: [],
            documents: [],
            selectedDoc: null,
            iframeUrl: "",
        });
        onWillStart(async () => {
            this.state.folders = await this.orm.searchRead(
                "guides.folder", [], ["id", "name", "complete_name", "parent_id"],
                { order: "complete_name" });
            this.state.documents = await this.orm.searchRead(
                "guides.document", [],
                ["id", "name", "folder_id", "version_count"], { order: "name" });
        });
    }

    docsForFolder(folderId) {
        return this.state.documents.filter(
            (d) => d.folder_id && d.folder_id[0] === folderId);
    }

    openDoc(doc) {
        this.state.selectedDoc = doc;
        this.state.iframeUrl = `/guides/render/${doc.id}`;
    }

    openFullscreen() {
        if (this.state.iframeUrl) {
            window.open(this.state.iframeUrl, "_blank");
        }
    }
}

registry.category("actions").add("guides_browser", GuidesBrowser);
```

- [ ] **Step 3: Create `static/src/guides_browser/guides_browser.xml`**

```xml
<?xml version="1.0" encoding="utf-8"?>
<templates xml:space="preserve">
    <t t-name="guides_html_sharing.GuidesBrowser">
        <div class="o_guides_browser d-flex">
            <div class="o_guides_sidebar">
                <h5 class="p-2">Guides</h5>
                <t t-foreach="state.folders" t-as="folder" t-key="folder.id">
                    <div class="o_guides_folder fw-bold px-2 pt-2"
                         t-esc="folder.complete_name"/>
                    <t t-foreach="docsForFolder(folder.id)" t-as="doc"
                       t-key="doc.id">
                        <div class="o_guides_doc px-3 py-1"
                             t-att-class="{ 'o_active': state.selectedDoc and state.selectedDoc.id === doc.id }"
                             t-on-click="() => this.openDoc(doc)"
                             t-esc="doc.name"/>
                    </t>
                </t>
            </div>
            <div class="o_guides_viewer flex-grow-1">
                <div t-if="state.selectedDoc" class="o_guides_toolbar p-2">
                    <strong t-esc="state.selectedDoc.name"/>
                    <button class="btn btn-sm btn-secondary float-end"
                            t-on-click="() => this.openFullscreen()">
                        Open Fullscreen
                    </button>
                </div>
                <iframe t-if="state.iframeUrl" t-att-src="state.iframeUrl"
                        sandbox="allow-scripts" class="o_guides_iframe"/>
                <div t-else="" class="text-muted p-4">
                    Select a document to preview.
                </div>
            </div>
        </div>
    </t>
</templates>
```

- [ ] **Step 4: Create `static/src/guides_browser/guides_browser.scss`**

```scss
.o_guides_browser {
    height: 100%;
    .o_guides_sidebar {
        width: 280px;
        border-right: 1px solid #dee2e6;
        overflow-y: auto;
        background: #f8f9fa;
    }
    .o_guides_doc {
        cursor: pointer;
        &:hover { background: #e9ecef; }
        &.o_active { background: #cfe2ff; font-weight: 600; }
    }
    .o_guides_viewer { display: flex; flex-direction: column; }
    .o_guides_iframe {
        flex-grow: 1;
        width: 100%;
        border: 0;
    }
}
```

- [ ] **Step 5: Add client action + menu** — append to `views/guides_menus.xml` (inside `<odoo>`):

```xml
    <record id="action_guides_browser" model="ir.actions.client">
        <field name="name">Guides Browser</field>
        <field name="tag">guides_browser</field>
    </record>
    <menuitem id="menu_guides_browser" name="Browser"
              parent="menu_guides_root" action="action_guides_browser"
              sequence="5"/>
```

And restore `web_icon="guides_html_sharing,static/description/icon.png"` on
`menu_guides_root`.

- [ ] **Step 6: Update + manual smoke**

```bash
docker compose exec -T odoo odoo -d postgres -u guides_html_sharing \
  --stop-after-init 2>&1 | tail -20
```

Then hard-refresh the browser, open **Guides → Browser**, confirm: folders and
their documents list on the left; clicking a document loads its HTML in the
sandboxed iframe; "Open Fullscreen" opens the render route in a new tab.

- [ ] **Step 7: Commit**

```bash
git add guides_html_sharing && git commit -m "feat(guides): OWL document browser client action with folder tree + iframe viewer"
```

---

### Task 12: Upload / inline-edit / restore UI wiring + final review

**Files:**
- Modify: `guides_html_sharing/views/guides_document_views.xml` (header buttons for upload/edit via a wizard OR document fields)
- Create: `guides_html_sharing/wizard/guides_version_wizard.py` + `wizard/guides_version_wizard_views.xml` + `wizard/__init__.py`
- Modify: `models/__init__.py`? (wizard is separate import in `__init__.py` of addon)
- Modify: `__init__.py` (`from . import wizard`), `__manifest__.py` (`data` add wizard view; `ir.model.access.csv` add wizard model), `tests/__init__.py`
- Test: extend `tests/test_document_version.py` with a wizard test

**Interfaces:**
- Produces: transient model `guides.version.wizard` with `document_id`, `mode` (`upload`/`inline`), `content_html` (Text), `upload_file` (Binary), `upload_filename` (Char), `changelog` (Char), method `action_save()` decoding the upload (base64 → utf-8) or using `content_html`, then calling `document_id.action_add_version(...)`. Document form header gets a "New Version" button opening the wizard.

- [ ] **Step 1: Write the failing test** — append to `tests/test_document_version.py`:

```python
    def test_wizard_upload_creates_version(self):
        import base64
        folder = self.env['guides.folder'].create({'name': 'WF'})
        doc = self.env['guides.document'].create({
            'name': 'WizDoc', 'folder_id': folder.id,
            'version_ids': [(0, 0, {'content_html': '<p>v1</p>'})]})
        wiz = self.env['guides.version.wizard'].create({
            'document_id': doc.id, 'mode': 'upload',
            'upload_file': base64.b64encode(b'<h1>uploaded</h1>'),
            'upload_filename': 'guide.html'})
        wiz.action_save()
        self.assertEqual(doc.content_html, '<h1>uploaded</h1>')
        self.assertEqual(doc.active_version_id.source, 'upload')
        self.assertEqual(doc.active_version_id.original_filename, 'guide.html')
```

- [ ] **Step 2: Run test to verify it fails** (standard `-u`). Expected: FAIL — wizard missing.

- [ ] **Step 3: Create `wizard/__init__.py`**

```python
# -*- coding: utf-8 -*-
from . import guides_version_wizard
```

- [ ] **Step 4: Create `wizard/guides_version_wizard.py`**

```python
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
```

- [ ] **Step 5: Create `wizard/guides_version_wizard_views.xml`**

```xml
<?xml version="1.0" encoding="utf-8"?>
<odoo>
    <record id="view_guides_version_wizard_form" model="ir.ui.view">
        <field name="name">guides.version.wizard.form</field>
        <field name="model">guides.version.wizard</field>
        <field name="arch" type="xml">
            <form string="New Version">
                <group>
                    <field name="mode" widget="radio"/>
                    <field name="upload_file" filename="upload_filename"
                           invisible="mode != 'upload'"
                           required="mode == 'upload'"/>
                    <field name="upload_filename" invisible="1"/>
                    <field name="content_html" invisible="mode != 'inline'"
                           widget="text"/>
                    <field name="changelog"/>
                </group>
                <footer>
                    <button name="action_save" type="object" string="Save"
                            class="btn-primary"/>
                    <button string="Cancel" class="btn-secondary"
                            special="cancel"/>
                </footer>
            </form>
        </field>
    </record>
</odoo>
```

- [ ] **Step 6: Add header button** to the document form (in `guides_document_views.xml` `<header>`):

```xml
                    <button name="%(action_guides_version_wizard)d" type="action"
                            string="New Version" class="btn-secondary"
                            context="{'default_document_id': id}"/>
```

And define the wizard action in `wizard/guides_version_wizard_views.xml`:

```xml
    <record id="action_guides_version_wizard" model="ir.actions.act_window">
        <field name="name">New Version</field>
        <field name="res_model">guides.version.wizard</field>
        <field name="view_mode">form</field>
        <field name="target">new</field>
    </record>
```

- [ ] **Step 7: Wire imports/manifest/ACL**

`__init__.py`:

```python
# -*- coding: utf-8 -*-
from . import models
from . import controllers
from . import wizard
```

`ir.model.access.csv` add:

```csv
access_guides_version_wizard_user,guides.version.wizard user,model_guides_version_wizard,guides_html_sharing.group_guides_user,1,1,1,1
```

`__manifest__.py` `data`: add `'wizard/guides_version_wizard_views.xml',` before
`views/guides_document_views.xml`.

- [ ] **Step 8: Run full suite** (no `--no-http`, standard `-u` + tests). Expected: `0 failed, 0 error(s)`.

- [ ] **Step 9: Plan self-review checklist (manual)** — confirm against the spec:
  - folders/subfolders + ACL ✓ (T3/T5), versioning + latest/restore ✓ (T4/T12),
    tags + project/task link + access from task ✓ (T6 tags, T7), roles
    admin/viewer/user ✓ (T5), creator/editors/followers/chatter ✓ (T4),
    request-edit-access activity ✓ (T8), public token portal-style link ✓ (T9),
    OWL left-nav + iframe viewer + fullscreen ✓ (T11), upload/inline edit ✓ (T12).

- [ ] **Step 10: Final manual smoke + commit**

Manual: full round-trip — create folder/doc, upload a real AI HTML file, view in
browser, enable public link, open it logged-out in a private window (only HTML
shows), request edit access as another user, approve as owner.

```bash
git add guides_html_sharing && git commit -m "feat(guides): version wizard for upload/inline edit + final wiring"
```

---

## Self-Review (author)

**Spec coverage:** every spec section maps to a task (see Task 12 Step 9). No gaps.

**Placeholder scan:** the Task 5 `create()` step intentionally shows a "cleaner
form" replacement block — the engineer replaces the Task 4 method wholesale; this
is explicit, not a placeholder. Icon generation (Task 11) and the task-form
`inherit_id` (Task 10) include concrete fallbacks. No `TBD`/`TODO` remain.

**Type consistency:** method names are stable across tasks — `action_add_version`,
`action_restore_version`, `_get_valid_shared_document`, `_is_share_valid`,
`action_request_edit_access`, `action_view_guides`, `user_can_contribute`,
`user_can_read`, `_get_effective_members`. Field names (`active_version_id`,
`content_html`, `share_token`, `share_active`, `share_expiry`, `editor_ids`,
`owner_id`) are used consistently in models, views, controllers, and the wizard.
