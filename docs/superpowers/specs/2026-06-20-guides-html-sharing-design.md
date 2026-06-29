# Guides HTML Sharing — Design

**Date:** 2026-06-20
**Addon:** `guides_html_sharing`
**Repo:** `odoo-dashboards`
**Odoo version:** 19.0 — License: LGPL-3

## Purpose

Internal documentation tool for an Odoo consultancy. Users upload AI-generated
HTML pages that explain how Odoo modules work, how to configure systems, etc.
Documents live in a folder/subfolder tree, are versioned, carry tags and an
optional link to a project/task, support per-document collaboration (owner,
editors, followers) with a chatter, and can be shared with external guests via a
tokenized public link that shows only the HTML.

## Scope & dependencies

Single Odoo addon. Depends on:

- `web` — OWL client action (the document browser UI)
- `mail` — chatter, activities, followers
- `project` — `project.project` / `project.task` relations and access from the task
- `portal` — public/tokenized sharing infrastructure

### Infrastructure wiring

- Repo `odoo-dashboards` is cloned into `addons/odoo-dashboards/` on the host,
  which maps to `/mnt/extra-addons/odoo-dashboards` in the container.
- `/mnt/extra-addons/odoo-dashboards` is added to `addons_path` in `odoo.conf`.
- The addon directory is `addons/odoo-dashboards/guides_html_sharing`.

### Out of scope (v1 / YAGNI)

- HTML is treated as a **single self-contained file** (inline CSS/JS or via CDN).
  No bundles with external asset files.
- No real rendered thumbnail image generation (no headless browser/wkhtmltoimage).
  The default "thumbnail" is the live sandboxed iframe, scaled/scrollable.

## Data model

### `guides.folder`

| Field | Type | Notes |
|-------|------|-------|
| `name` | Char | required |
| `parent_id` | Many2one `guides.folder` | hierarchical |
| `parent_path` | Char | `_parent_store = True` |
| `complete_name` | Char | computed, stored (full path) |
| `sequence` | Integer | ordering |
| `member_ids` | One2many `guides.folder.member` | per-folder ACL |
| `inherit_parent_access` | Boolean | default True; inherit parent folder members |
| `document_ids` | One2many `guides.document` | |

### `guides.folder.member`

Per-folder access control line.

| Field | Type | Notes |
|-------|------|-------|
| `folder_id` | Many2one `guides.folder` | required, ondelete cascade |
| `user_id` | Many2one `res.users` | required |
| `access_level` | Selection | `reader` / `contributor` |

`reader` can read documents in the folder; `contributor` can additionally create
documents in the folder. Effective access for a folder = its own members plus, if
`inherit_parent_access`, the resolved members of ancestor folders.

### `guides.document`

Inherits `mail.thread`, `mail.activity.mixin`.

| Field | Type | Notes |
|-------|------|-------|
| `name` | Char | title, required |
| `folder_id` | Many2one `guides.folder` | required |
| `owner_id` | Many2one `res.users` | default = create_uid; transferable |
| `editor_ids` | Many2many `res.users` | users allowed to edit this document |
| `tag_ids` | Many2many `guides.tag` | |
| `project_id` | Many2one `project.project` | optional |
| `task_id` | Many2one `project.task` | optional; sets `project_id` |
| `version_ids` | One2many `guides.document.version` | |
| `active_version_id` | Many2one `guides.document.version` | the latest/current version shown |
| `version_count` | Integer | computed |
| `content_html` | Html/Text | related to `active_version_id.content_html` (readonly convenience) |
| `share_token` | Char | random, indexed |
| `share_active` | Boolean | public link enabled |
| `share_expiry` | Datetime | optional expiration |
| `active` | Boolean | archiving |

Followers (native `message_follower_ids`/`message_partner_ids`) are the
"seguidores". Viewers see documents where they are followers.

### `guides.document.version`

Immutable snapshot of content.

| Field | Type | Notes |
|-------|------|-------|
| `document_id` | Many2one `guides.document` | required, ondelete cascade |
| `version_number` | Integer | sequential per document |
| `content_html` | Text | the full HTML page |
| `source` | Selection | `upload` / `inline` |
| `original_filename` | Char | for uploads |
| `changelog` | Char/Text | optional note |
| `create_uid` / `create_date` | — | who uploaded / when |

### `guides.tag`

| Field | Type | Notes |
|-------|------|-------|
| `name` | Char | required, unique |
| `color` | Integer | |

Covers "tipo" and any free-form tags. `project_id`/`task_id` are modeled as
explicit relations, not tags.

### `guides.access.request`

| Field | Type | Notes |
|-------|------|-------|
| `document_id` | Many2one `guides.document` | required |
| `user_id` | Many2one `res.users` | requester |
| `state` | Selection | `pending` / `approved` / `rejected` |
| `note` | Text | optional message from requester |

## Permissions

Three groups (implied chain): `group_guides_viewer` ⊂ `group_guides_user` ⊂
`group_guides_admin`.

- **Viewer** — reads documents where they are a follower.
- **User** — viewer rights, plus: reads folders/documents where they have folder
  access (reader or contributor); **creates** documents only in folders where
  they are a `contributor` (enforced in `create()`); **edits** documents where
  they are `owner_id` or in `editor_ids`.
- **Admin** — full read/write on all folders, documents, versions, tags
  (global record rules).

### Record rules

- `guides.document` read (user, non-admin): follower **OR** folder access **OR**
  owner **OR** editor.
- `guides.document` write (user, non-admin): owner **OR** editor.
- `guides.document` create: gated in `create()` by verifying contributor access
  on the target folder (record rules cannot express folder-based create gating
  cleanly); admin bypasses.
- Admin group: global read/write rules on all models.

`ir.model.access.csv` grants base table CRUD per group; record rules narrow rows.

## UI — OWL client action `guides_browser`

Full-screen client action under an application menu **"Guides"**.

- **Left sidebar:** recursive folder/subfolder tree with the documents listed
  under each folder; search box; "New folder" / "New document" buttons shown
  according to permissions.
- **Right panel:** on selecting a document — header (title, tags, project/task
  links, version selector, action buttons) and a body that renders the active
  version's HTML inside a sandboxed iframe (`sandbox="allow-scripts"`, no
  `allow-same-origin`) served by a controller. The iframe doubles as the default
  scaled "thumbnail"; a button opens it full-screen.
- **Action buttons:** Edit HTML (inline code editor → saves a new version),
  Upload new version (`.html` file), Request edit access, Share link, open
  chatter, and a version dropdown to view previous versions read-only with a
  "restore" action (owner/editor/admin) that creates a new version from the old
  content.

Data is read/written via the `orm` service (`call_kw`).

## Controllers (HTTP)

- `GET /guides/render/<int:document_id>` and
  `GET /guides/render/<int:document_id>/v/<int:version_id>` — `auth='user'`,
  enforces ACL via `sudo()` after an access check, returns the version HTML for
  the backend iframe, with a restrictive `Content-Security-Policy`.
- `GET /guides/public/<string:token>` — `auth='public'`, validates that
  `share_active` is set, the token matches, and `share_expiry` (if set) has not
  passed; returns **only the HTML** of the active version (no Odoo chrome), with
  CSP headers. Token is revocable/regenerable.

### Security notes

- Serving user-supplied HTML on the Odoo domain carries XSS risk. The backend
  iframe uses the `sandbox` attribute (scripts allowed, same-origin denied) so
  embedded scripts cannot reach the Odoo session. The public route is a
  standalone page with CSP headers. Acceptable for an internal tool; documented
  explicitly.

## Project integration

- `project.task` (and optionally `project.project`): a smart button / notebook
  page listing related `guides.document` records, opening them in the browser.
- On the document, setting `task_id` auto-fills `project_id`.

## Versioning & access-request flow

- Creating a document creates version 1. Editing inline or uploading creates
  version N+1 and updates `active_version_id`. The latest is always shown;
  previous versions are read-only with a "restore" action.
- **Request edit access:** a user who can read but not write clicks the button →
  creates a `guides.access.request` (pending) and schedules a To-Do
  `mail.activity` on the document for `owner_id`. On approval the requester is
  added to `editor_ids`, the request is marked approved, the activity is marked
  done, and the requester is notified.

## Addon structure

```
guides_html_sharing/
  __init__.py
  __manifest__.py
  models/
    __init__.py
    guides_folder.py
    guides_folder_member.py
    guides_document.py
    guides_document_version.py
    guides_tag.py
    guides_access_request.py
    project_task.py
  controllers/
    __init__.py
    main.py
  security/
    guides_security.xml      # groups + record rules
    ir.model.access.csv
  views/
    guides_menus.xml
    guides_document_views.xml
    guides_folder_views.xml
    guides_tag_views.xml
    project_task_views.xml
    guides_templates.xml      # public/portal page
  data/
    guides_data.xml           # sequences, activity type
  static/src/guides_browser/
    guides_browser.js
    guides_browser.xml
    guides_browser.scss
```

## Testing

- Odoo `TransactionCase` tests: role/folder permission matrix (viewer/user/admin
  + folder reader/contributor), version creation and `active_version_id`
  bookkeeping, public token validity and expiration.
- Manual verification of the OWL browser UI (tree navigation, iframe render,
  inline edit, upload, share link, request-access flow).
