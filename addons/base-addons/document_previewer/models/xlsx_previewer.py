from odoo import models, fields
import base64
from urllib.parse import quote

class XlsxPreviewer(models.TransientModel):
    _name = "xlsx.previewer"
    _description = "Xlsx Previewer"

    iframe = fields.Html(sanitize = False, compute="get_iframe")
    attachment_id = fields.Many2one('ir.attachment')

    def get_iframe(self):
        for obj in self:
            base_url = self.sudo().env["ir.config_parameter"].get_param("web.base.url")
            download_url = "/web/content/" + str(obj.attachment_id.id)

            obj.iframe = '<iframe src="https://view.officeapps.live.com/op/embed.aspx?src={}"></iframe>'.format(base_url + download_url)

    def open_preview(self, action_id, model_id, data):
        
        report = self.env.ref(action_id)

        for key in data:
            if data.get(key):
                data.update({key: str(data.get(key))})
        
        report_content = report._render_xlsx(report.report_name, model_id.id, data)[0]

        if '%' in report.print_report_name:
            globalsParameter = {"__builtins__": None}
            localsParameter = {"object": model_id, "name": ""}
            report_name = exec(
                "name = " + report.print_report_name, globalsParameter, localsParameter
            )
            report_name = localsParameter.get("name", report.name)
        else:
            report_name = report.print_report_name

        xlsxPreviewer = self.create({})

        attachment = self.env["ir.attachment"].create(
            {"name": report_name, "datas": base64.b64encode(report_content), "res_id": xlsxPreviewer.id, "res_model": self._name, "public": True}
        )

        xlsxPreviewer.write({"attachment_id": attachment.id})
        
        return {
            "name": "Preview Xlsx:",
            "type": "ir.actions.act_window",
            "view_mode": "form",
            "res_model": "xlsx.previewer",
            "res_id": xlsxPreviewer.id,
            "target": "new",
        }
    
    def download_file(self):
        
        base_url = self.sudo().env["ir.config_parameter"].get_param("web.base.url")
        download_url = "/web/content/" + str(self.attachment_id.id) + "?download=true"

        return {
            "type": "ir.actions.act_url",
            "url": str(base_url) + str(download_url),
            "target": "self",
        }
    
    # def remove_old_attachment(self):
    #     attachments = self.sudo().env['ir.attachment'].search([("res_model", "=", self._name)])
    #     for attachment in attachments:
    #         attachment.unlink()

    def open_preview_attachment(self, attachment_id, remove=False):
        if remove:
            attachment_id.res_model = self._name
        attachment_id.public = True
        xlsxPreviewer = self.create({"attachment_id": attachment_id.id})

        return {
            "name": "Preview Xlsx:",
            "type": "ir.actions.act_window",
            "view_mode": "form",
            "res_model": "xlsx.previewer",
            "res_id": xlsxPreviewer.id,
            "target": "new",
        }
