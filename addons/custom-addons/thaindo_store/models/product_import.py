from odoo import models, fields, api
from odoo.exceptions import ValidationError
from datetime import datetime, timedelta

class ProductImportLine(models.Model):
    _name = "product.import.line"
    _description = "Product Import Line"

    import_id = fields.Many2one("product.import")
    product_id = fields.Many2one("product.product", "สินค้า")
    qty = fields.Float("จำนวน")
    price = fields.Float("ราคาต่อหน่วย (บาท)")
    uom_id = fields.Many2one("uom.uom", related="product_id.uom_id", string="หน่วยวัด")
    categ_id = fields.Char(related="product_id.categ_id.name", string="หมวดหมู่")

    @api.onchange("product_id")
    def _change_product_id(self):
        for obj in self:
            obj.price = obj.product_id.standard_price

    @api.constrains("qty", "price")
    def _check(self):
        for obj in self:
            if obj.qty <= 0:
                raise ValidationError("จำนวนนำเข้าต้องมากกว่า 0")
            if obj.price < 0:
                raise ValidationError("ราคาต่อหน่วยนำเข้าต้องมากกว่า 0")

class ProductImport(models.Model):
    _name = "product.import"
    _description = "รายการนำเข้า"
    _inherit = ["mail.thread", "mail.activity.mixin"]

    name = fields.Char(default="New")
    user_id = fields.Many2one(
        "res.users", string="ผู้รับผิดชอบ", default=lambda l: l.env.user.id
    )
    doc_ref = fields.Char("เอกสารต้นทาง (ถ้ามี)")
    datetime = fields.Datetime("วันที่ทำรายการ", default=lambda l: fields.Datetime.now())
    line_ids = fields.One2many("product.import.line", "import_id")
    state = fields.Selection(
        [
            ("draft", "ร่าง"),
            ("to_approve", "รออนุมัติ"),
            ("approve", "อนุมัติ"),
            ("cancel", "ยกเลิก"),
        ],
        default="draft",
        string="สถานะ",
    )
    note = fields.Char('หมายเหตุ')

    @api.constrains("line_ids", "datetime")
    def _check(self):
        for obj in self:
            if not obj.line_ids:
                raise ValidationError("ยังไม่ระบุสินค้านำเข้า")
            if obj.datetime > datetime.now():
                raise ValidationError("ไม่สามารถทำรายการนำเข้าล่วงหน้าได้")
            if obj.datetime < datetime.today() - timedelta(days=15):
                raise ValidationError("ไม่สามารถทำรายการนำเข้าล้าช้ากว่า 15 วันได้")

    def action_validate(self):
        self.name = self.env["ir.sequence"].next_by_code("product.import")
        self.state = "approve"

        check_duplicate = []
        for line in self.line_ids:
            if line.product_id.name in check_duplicate:
                raise ValidationError("มีสินค้าซ้ำในรายการ")
            else:
                check_duplicate.append(line.product_id.name)

        for line in self.line_ids:
            product_id = line.product_id
            if product_id.standard_price != line.price:
                self.env["product.price.line"].create(
                    {
                        "product_id": product_id.product_tmpl_id.id,
                        "import_id": line.import_id.id,
                        "datetime": line.import_id.datetime,
                        "price": line.price,
                    }
                )
                product_id.with_context(is_import=True).write(
                    {"standard_price": line.price}
                )

            new_qty = product_id.qty_available + line.qty
            warehouse = self.env["stock.warehouse"].search(
                [("company_id", "=", self.env.company.id)], limit=1
            )
            self.env["stock.quant"].with_context(inventory_mode=True).create(
                {
                    "product_id": product_id.id,
                    "location_id": warehouse.lot_stock_id.id,
                    "inventory_quantity": new_qty,
                }
            )._apply_inventory()

    def action_cancel(self):
        self.name = self.env["ir.sequence"].next_by_code("product.import")
        self.state = "cancel"
