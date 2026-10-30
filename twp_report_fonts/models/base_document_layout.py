from odoo import api, fields, models


class BaseDocumentLayout(models.TransientModel):
    _inherit = "base.document.layout"

    # The preview renders web.styles_company_report with the wizard standing in
    # for the company, so the field keeps the company's name.
    twp_heading_font = fields.Selection(related="company_id.twp_heading_font", readonly=False)

    @api.depends("twp_heading_font")
    def _compute_preview(self):
        return super()._compute_preview()
