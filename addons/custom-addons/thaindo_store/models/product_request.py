from odoo import models, fields, api
from odoo.exceptions import ValidationError
from datetime import datetime, timedelta

class ProductRequestLine(models.Model):
    _name = "product.request.line"
    _description = "Product Request Line"

    request_id = fields.Many2one("product.request")
    product_id = fields.Many2one("product.product", "สินค้า")
    qty = fields.Float("จำนวน")
    uom_id = fields.Many2one("uom.uom", related="product_id.uom_id", string="หน่วยวัด")
    categ_id = fields.Char(related="product_id.categ_id.name", string="หมวดหมู่")

    @api.constrains("qty")
    def _check(self):
        for obj in self:
            if obj.qty <= 0:
                raise ValidationError("จำนวนเบิกต้องมากกว่า 0")

class ProductRequest(models.Model):
    _name = "product.request"
    _description = "รายการเบิก"
    _inherit = ["mail.thread", "mail.activity.mixin"]

    company_id = fields.Many2one('res.company', default=lambda l: l.env.company.id)
    name = fields.Char(default="New")
    user_id = fields.Many2one(
        "res.users", string="ผู้รับผิดชอบ", default=lambda l: l.env.user.id
    )
    doc_ref = fields.Char("เอกสารต้นทาง (ถ้ามี)")
    datetime = fields.Datetime("วันที่ทำรายการ", default=lambda l: fields.Datetime.now())
    line_ids = fields.One2many("product.request.line", "request_id")
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
    department_id = fields.Many2one("hr.department", "แผนกที่ขอเบิก")
    note = fields.Char("หมายเหตุ")
    purpose = fields.Char('วัตถุประสงค์')

    @api.constrains("line_ids", "datetime")
    def _check(self):
        for obj in self:
            if not obj.line_ids:
                raise ValidationError("ยังไม่ระบุสินค้าเบิก")
            if obj.datetime > datetime.now():
                raise ValidationError("ไม่สามารถทำรายการเบิกล่วงหน้าได้")
            if obj.datetime < datetime.today() - timedelta(days=15):
                raise ValidationError("ไม่สามารถทำรายการเบิกล้าช้ากว่า 15 วันได้")

    def action_validate(self):
        self.name = self.env["ir.sequence"].next_by_code("product.request")
        self.state = "approve"

        insufficient = []
        check_duplicate = []
        for line in self.line_ids:
            product_id = line.product_id
            new_qty = product_id.qty_available - line.qty
            if new_qty < 0:
                insufficient.append(product_id.name)
            if product_id.name in check_duplicate:
                raise ValidationError("มีสินค้าซ้ำในรายการ")
            else:
                check_duplicate.append(product_id.name)

        if insufficient:
            raise ValidationError("จำนวนสินค้าในระบบไม่พอ ดังนี้\n - " + "\n - ".join(insufficient))

        for line in self.line_ids:
            product_id = line.product_id
            new_qty = product_id.qty_available - line.qty
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
        self.name = self.env["ir.sequence"].next_by_code("product.request")
        self.state = "cancel"

    def print_report(self):
        return self.env["pdf.previewer"].open_action(
            self, "thaindo_store.action_product_request_report"
        )
