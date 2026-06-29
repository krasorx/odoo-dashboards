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
