from odoo import models, fields

class IrUIMenu(models.Model):
    _inherit = 'ir.ui.menu'

    external_id = fields.Char(compute="_compute_external_id")

    def _compute_external_id(self):
        for obj in self:
            obj.external_id = obj.get_external_id()