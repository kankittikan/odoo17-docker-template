from odoo import models, fields

class ProductCategory(models.Model):
    _inherit = 'product.category'

    active = fields.Boolean(default=True)