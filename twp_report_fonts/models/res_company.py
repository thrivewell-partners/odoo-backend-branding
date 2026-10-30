from odoo import api, fields, models

# Selection value, which is also the @font-face family name in
# static/src/scss/report_fonts.scss, the way Odoo names "Open_Sans". A new
# font is its files under static/fonts/<value>/, its faces in that file and
# a line here.
FONTS = {
    "Barlow": "Barlow",
    "Barlow_Semi_Condensed": "Barlow Semi Condensed",
}


class ResCompany(models.Model):
    _inherit = "res.company"

    font = fields.Selection(
        selection_add=list(FONTS.items()),
        ondelete={key: "set default" for key in FONTS},
    )
    twp_heading_font = fields.Selection(
        selection="_twp_heading_font_selection",
        string="Heading Font",
        help="Font for titles and headings on PDF documents. Blank uses the text font.",
    )

    @api.model
    def _twp_heading_font_selection(self):
        return self._fields["font"].selection

    @api.model_create_multi
    def create(self, vals_list):
        companies = super().create(vals_list)
        if any(vals.get("twp_heading_font") for vals in vals_list):
            self._update_asset_style()
        return companies

    def write(self, vals):
        res = super().write(vals)
        # Odoo rewrites the company style sheet only for its own style fields.
        if "twp_heading_font" in vals:
            self._update_asset_style()
            self.env.registry.clear_cache("assets")
        return res
