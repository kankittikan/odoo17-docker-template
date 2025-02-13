from odoo import models, fields

class HrDepartment(models.Model):
    _inherit = 'hr.department'

    display_name = fields.Char(related="name")