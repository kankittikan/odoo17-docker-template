from odoo.tools.misc import xlsxwriter
from odoo import models, fields, api
from datetime import datetime
from odoo.exceptions import UserError
import pytz


class XlsxwriterStockImportReportWizard(models.TransientModel):
    _name = "xlsx.stock.import.report.wizard"

    date_start = fields.Date(string="Start Date")
    date_end = fields.Date(string="End Date", default=lambda l: fields.Date.today())
    categ_ids = fields.Many2many(
        "product.category", "stock_import_categtory_rel", string="หมวดหมู่"
    )
    user_id = fields.Many2one("res.users", default=lambda l: l.env.user)

    def print_xlsx(self):
        data = {
            "date_start": self.date_start,
            "date_end": self.date_end,
            "categ_ids": ", ".join([i.name for i in self.categ_ids]),
            "categ_ids_id": self.categ_ids.ids,
        }

        return self.env["xlsx.previewer"].open_preview(
            "thaindo_store.action_xlsx_stock_import_report", self, data
        )


class XlsxStockImportReport(models.AbstractModel):
    _name = "report.xlsx_stock_import_report"
    _inherit = "report.report_xlsx.abstract"

    def generate_xlsx_report(self, workbook, data, lines):
        DEFAULTCOLUMNWIDTH = 22
        report_name = "รายงานรายการนำเข้า"
        sheet = workbook.add_worksheet(report_name)
        # column_header_row_index = 4
        column_headers_vals = [
            "ลำดับ",
            "เลขที่เอกสาร",
            "วันที่นำเข้า",
            "ผู้นำเข้า",
            "ชื่อสินค้า",
            "หมวดหมู่",
            "จำนวนที่นำเข้า",
            "หน่วยวัด",
            "ราคาต่อหน่วย",
            "หมายเหตุ",
            "เอกสารต้นทาง",
        ]

        last_col = len(column_headers_vals)
        last_col_index = last_col - 1

        company_name_format = workbook.add_format(
            {"bold": True, "font_size": 15, "align": "left", "border": 2}
        )
        report_name_format = workbook.add_format(
            {"font_size": 15, "align": "left", "border": 2}
        )
        header_string_value_format = workbook.add_format(
            {"font_size": 11, "align": "left", "border": 2}
        )
        column_header_format = workbook.add_format(
            {"font_size": 11, "bold": True, "align": "center", "border": 2}
        )

        # Set Column
        sheet.set_column(0, 0, 8)
        sheet.set_column(1, last_col, DEFAULTCOLUMNWIDTH)

        # Row1: show company name
        sheet.merge_range(
            0, 0, 0, last_col_index, self.env.user.company_id.name, company_name_format
        )

        # Row2: report name
        sheet.merge_range(1, 0, 1, last_col_index, report_name, report_name_format)

        # Row3: show print date
        user_tz = self.env.user.tz or "UTC"  # Get user's timezone or use UTC as default
        tz = pytz.timezone(user_tz)
        print_by = self.env.user.name
        print_datetime = datetime.now().astimezone(tz).strftime("%d/%m/%Y %H:%M:%S")
        sheet.write(2, last_col - 4, "พิมพ์โดย", column_header_format)
        sheet.write(2, last_col - 3, print_by, header_string_value_format)
        sheet.write(2, last_col - 2, "พิมพ์ ณ วันที่", column_header_format)
        sheet.write(2, last_col - 1, print_datetime, header_string_value_format)

        condition_col = 0
        if data.get("date_start"):
            date_condition = datetime.strptime(
                data.get("date_start"), "%Y-%m-%d"
            ).strftime("%d/%m/%Y")
            sheet.write(2, condition_col, "วันเริ่มต้น", column_header_format)
            sheet.write(
                2, condition_col + 1, date_condition, header_string_value_format
            )
            condition_col += 2
        if data.get("date_end"):
            date_condition = datetime.strptime(
                data.get("date_end"), "%Y-%m-%d"
            ).strftime("%d/%m/%Y")
            sheet.write(2, condition_col, "วันสิ้นสุด", column_header_format)
            sheet.write(
                2, condition_col + 1, date_condition, header_string_value_format
            )
            condition_col += 2
        if data.get("categ_ids"):
            sheet.write(2, condition_col, "หมวดหมู่", column_header_format)
            sheet.write(
                2,
                condition_col + 1,
                data.get("categ_ids"),
                header_string_value_format,
            )
            condition_col += 2

        # Row4: show column name
        for count, value in enumerate(column_headers_vals):
            sheet.merge_range(3, count, 4, count, value, column_header_format)

        # Row 5 - ... : show lines
        lines = self.get_lines(workbook, data)
        begin_line_row = 5
        for line_details in lines:
            for count_ld, ld in enumerate(line_details):
                value = ld[1]
                format_value = ld[2]
                sheet.write(begin_line_row, count_ld, value, format_value)
            begin_line_row += 1

    def get_lines(self, workbook, data):
        detail_string_format = workbook.add_format(
            {
                "font_size": 9,
                "align": "left",
            }
        )
        detail_date_format = workbook.add_format(
            {
                "font_size": 9,
                "num_format": "dd/mm/yyyy",
                "align": "center",
            }
        )
        detail_datetime_format = workbook.add_format(
            {
                "font_size": 9,
                "num_format": "dd/mm/yyyy HH:MM:SS",
                "align": "center",
            }
        )
        detail_number_format = workbook.add_format(
            {
                "font_size": 9,
                "num_format": "#,##0.00",
                "align": "right",
            }
        )
        detail_sum_number_format = workbook.add_format(
            {"font_size": 9, "num_format": "#,##0.00", "align": "right", "bold": True}
        )
        detail_sequence_format = workbook.add_format(
            {
                "font_size": 9,
                "align": "center",
            }
        )

        dom_transaction = [("import_id.datetime", "<=", data.get("date_end")), ("import_id.state", "=", "approve")]
        if data.get("date_start"):
            dom_transaction.append(
                ("import_id.datetime", ">=", data.get("date_start"))
            )
        if data.get("categ_ids_id"):
            dom_transaction.append(
                ("product_id.categ_id", "in", eval(data.get("categ_ids_id")))
            )
        product_import_lines = self.env["product.import.line"].search(dom_transaction)

        if not product_import_lines:
            raise UserError("ไม่พบรายการ")

        product_import_lines = sorted(
            product_import_lines, key=lambda x: x.import_id.name
        )

        lines = []
        no = 1
        for line in product_import_lines:

            items = [
                ("no", no, detail_sequence_format),
                ("request_name", line.import_id.name, detail_string_format),
                ("request_datetime", line.import_id.datetime, detail_datetime_format),
                ("user_id", line.import_id.user_id.name, detail_string_format),
                ("product_name", line.product_id.name, detail_string_format),
                ("product_categ", line.product_id.categ_id.name, detail_string_format),
                ("product_qty", line.qty, detail_number_format),
                ("product_uom", line.uom_id.name, detail_string_format),
                ("product_price", line.price, detail_number_format),
                ("note", line.import_id.note or '', detail_string_format),
                ("doc_ref", line.import_id.doc_ref or '', detail_string_format),
            ]
            lines.append(items)
            no += 1

        return lines
