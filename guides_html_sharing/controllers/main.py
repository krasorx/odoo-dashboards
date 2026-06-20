# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request


def _html_response(html):
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
