# -*- coding: utf-8 -*-
from odoo import models


class IrHttp(models.AbstractModel):
    _inherit = 'ir.http'

    def session_info(self):
        result = super().session_info()
        models_with_kpis = self.env['kpi.widget'].sudo().search([
            ('active', '=', True),
        ]).mapped('model_name')
        result['kpi_models'] = sorted(set(m for m in models_with_kpis if m))
        return result
