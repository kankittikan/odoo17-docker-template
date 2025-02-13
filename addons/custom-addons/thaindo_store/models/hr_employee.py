from odoo import models, fields, api

class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    nickname = fields.Char('ชื่อเล่น', tracking=True)