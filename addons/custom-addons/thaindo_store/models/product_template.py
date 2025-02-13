from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError


class ProductTemplate(models.Model):
    _inherit = "product.template"

    min_quantity = fields.Float(string="จำนวนขั้นต่ำ", tracking=True)
    price_line_ids = fields.One2many("product.price.line", "product_id")
    note = fields.Char('หมายเหตุ')
    is_below_min_quantity = fields.Boolean(compute="_compuite_is_below_min_quantity", store=True)
    categ_id = fields.Many2one('product.category', default=False)
    uom_id = fields.Many2one('uom.uom', default=False)
    detailed_type = fields.Selection(default="product")

    @api.constrains("name")
    def _check_name(self):
        for obj in self:
            if len(obj.env['product.template'].search([("name", "=", obj.name)])) > 1:
                raise ValidationError("มีชื่อสินค้าซ้ำในระบบ")
            
    @api.depends("qty_available", "min_quantity")
    def _compuite_is_below_min_quantity(self):
        for obj in self:
            obj.is_below_min_quantity = obj.qty_available < obj.min_quantity

    @api.constrains("min_quantity", "standard_price")
    def _check(self):
        for obj in self:
            if obj.min_quantity < 0:
                raise UserError("จำนวนขั้นต่ำต้องมากกว่า 0")
            if obj.standard_price < 0:
                raise UserError("ราคาต่อหน่วยห้ามต่ำกว่า 0")

    def write(self, vals):
        if "standard_price" in vals and vals.get("standard_price") >= 0 and not self.env.context.get('is_import'):
            self.env["product.price.line"].create(
                {
                    "product_id": self.id,
                    "datetime": fields.Datetime.now(),
                    "price": vals.get("standard_price"),
                }
            )

        return super(ProductTemplate, self).write(vals)


class ProductPriceLine(models.Model):
    _name = "product.price.line"
    _description = "Product Price Line"

    product_id = fields.Many2one("product.template")
    import_id = fields.Many2one("product.import", "เลขที่นำเข้า")
    datetime = fields.Datetime("เปลี่ยนแปลงเมื่อ")
    price = fields.Float("ราคา (บาท)")
