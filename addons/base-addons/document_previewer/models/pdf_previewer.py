from odoo import fields, models, api
import base64
from odoo.exceptions import UserError

class PdfPreviewer(models.TransientModel):
    _name = "pdf.previewer"
    _description = "Form for preview PDF before print"

    model_id = fields.Integer()
    model_name = fields.Char()
    attachment_id = fields.Many2one('ir.attachment')
    report_name = fields.Char(related="attachment_id.name", string="Report")
    show_binary = fields.Binary(related="attachment_id.datas", readonly=True)
    select_report = fields.Many2one('ir.actions.report', domain='[("model", "=", model_name),("binding_model_id", "!=", False)]', string="Select Report")
    
    skip_render_content = fields.Json()
    
    def open_preview_attachment(self, attachment_id, remove=False):
        if remove:
            attachment_id.res_model = self._name
        pdfPreviewer = self.create({"attachment_id": attachment_id.id})

        return {
            "name": "Preview PDF:",
            "type": "ir.actions.act_window",
            "view_mode": "form",
            "res_model": "pdf.previewer",
            "res_id": pdfPreviewer.id,
            "target": "new",
        }
    
    def open_action(self, model_id, action_id):
        
        qweb_report_id = self.env.ref(action_id)
        pdf_content = qweb_report_id._render_qweb_pdf(
            qweb_report_id.report_name, [model_id.id]
        )[0]

        if '%' in qweb_report_id.print_report_name:
            globalsParameter = {"__builtins__": None}
            localsParameter = {"object": model_id, "name": ""}
            report_name = exec(
                "name = " + qweb_report_id.print_report_name, globalsParameter, localsParameter
            )
            report_name = localsParameter.get("name", qweb_report_id.name)
        else:
            report_name = qweb_report_id.print_report_name

        attachment = self.env["ir.attachment"].create(
            {"name": report_name, "datas": base64.b64encode(pdf_content), "res_model": self._name}
        )

        pdfPreviewer = self.create(
            {"attachment_id": attachment.id}
        )
        return {
            "name": "Preview PDF:",
            "type": "ir.actions.act_window",
            "view_mode": "form",
            "res_model": "pdf.previewer",
            "res_id": pdfPreviewer.id,
            "target": "new",
        }

    def download_file(self):
        if not self.attachment_id:
            raise UserError("No Report Select")
        
        base_url = self.sudo().env["ir.config_parameter"].get_param("web.base.url")
        download_url = "/web/content/" + str(self.attachment_id.id) + "?download=true"

        return {
            "type": "ir.actions.act_url",
            "url": str(base_url) + str(download_url),
            "target": "self",
        }
    
    def open_select_report_wizard(self, model_id, skip_render_content=False):

        # check one report
        check_one_report = self.env['ir.actions.report'].search([("model", "=", model_id._name),("binding_model_id", "!=", False)])
        if len(check_one_report) == 1:
            return self.open_action(model_id, list(check_one_report.get_external_id().values())[0])

        pdfPreviewer = self.create(
            {"model_id": model_id.id, "model_name": model_id._name, "skip_render_content": skip_render_content}
        )
        
        return {
            "name": "Preview PDF:",
            "type": "ir.actions.act_window",
            "view_mode": "form",
            "res_model": "pdf.previewer",
            "res_id": pdfPreviewer.id,
            "target": "new",
        }
    
    def load_report(self):

        if not self.select_report:
            raise UserError("No Report Select")
        
        report = self.select_report
        pdf_content = None

        skip_report_ids = None
        report_external_id = list(report.get_external_id().values())[0]
        if self.skip_render_content:
            skip_report_ids = list(self.skip_render_content.keys())

        if self.skip_render_content and report_external_id in skip_report_ids:
            obj = self.env[self.model_name].browse(self.model_id)
            pdf_content = eval('obj.{}()'.format(self.skip_render_content.get(report_external_id)))
        else:
            pdf_content = report._render_qweb_pdf(report.report_name, [self.model_id])[0]

        globalsParameter = {"__builtins__": None}
        localsParameter = {"object": self.env[self.model_name].browse(self.model_id), "name": ""}
        report_name = exec(
            "name = " + report.print_report_name, globalsParameter, localsParameter
        )
        report_name = localsParameter.get("name", report.name)

        attachment = self.env["ir.attachment"].create(
            {"name": report_name, "datas": base64.b64encode(pdf_content), "res_model": self._name}
        )
        self.write({"attachment_id": attachment})

        return {
            "name": "Preview PDF:",
            "type": "ir.actions.act_window",
            "view_mode": "form",
            "res_model": "pdf.previewer",
            "res_id": self.id,
            "target": "new",
        }
    
    def remove_old_attachment(self):
        attachments = self.sudo().env['ir.attachment'].search([("res_model", "in", [self._name, 'xlsx.previewer'])])
        for attachment in attachments:
            attachment.unlink()