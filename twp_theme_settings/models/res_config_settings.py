from odoo import _, api, fields, models
from odoo.exceptions import UserError
from odoo.http import request

from .colors import is_hex
from .twp_theme import PALETTE, PREFIX

COLOR_FIELDS = [f"twp_{key}" for key in PALETTE] + [f"twp_dark_{key}" for key in PALETTE]
CHECKED_COLORS = COLOR_FIELDS + ["twp_staging_color", "twp_login_bg"]
# The settings a look file carries between databases. Staging marking belongs
# to one database, and company colours and logos to its companies.
LOOK_FIELDS = COLOR_FIELDS + [
    "twp_dark_enabled", "twp_dark_default",
    "twp_font_body", "twp_font_head", "twp_font_size", "twp_radius",
    "twp_density", "twp_sheet_width",
    "twp_login_enabled", "twp_login_layout", "twp_login_bg", "twp_login_heading",
    "twp_login_tagline", "twp_login_logo", "twp_login_background",
]


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    # Light palette. Blank keeps Odoo's own colour.
    twp_primary = fields.Char("Primary", config_parameter=PREFIX + "primary")
    twp_navbar = fields.Char("Navbar", config_parameter=PREFIX + "navbar")
    twp_success = fields.Char("Success", config_parameter=PREFIX + "success")
    twp_info = fields.Char("Info", config_parameter=PREFIX + "info")
    twp_warning = fields.Char("Warning", config_parameter=PREFIX + "warning")
    twp_danger = fields.Char("Danger", config_parameter=PREFIX + "danger")
    twp_bg = fields.Char("Page background", config_parameter=PREFIX + "bg")
    twp_view = fields.Char("Sheets", config_parameter=PREFIX + "view")
    twp_text = fields.Char("Text", config_parameter=PREFIX + "text")

    # Dark palette. Blank is worked out from the light colour.
    twp_dark_primary = fields.Char("Primary, dark", config_parameter=PREFIX + "dark_primary")
    twp_dark_navbar = fields.Char("Navbar, dark", config_parameter=PREFIX + "dark_navbar")
    twp_dark_success = fields.Char("Success, dark", config_parameter=PREFIX + "dark_success")
    twp_dark_info = fields.Char("Info, dark", config_parameter=PREFIX + "dark_info")
    twp_dark_warning = fields.Char("Warning, dark", config_parameter=PREFIX + "dark_warning")
    twp_dark_danger = fields.Char("Danger, dark", config_parameter=PREFIX + "dark_danger")
    twp_dark_bg = fields.Char("Page background, dark", config_parameter=PREFIX + "dark_bg")
    twp_dark_view = fields.Char("Sheets, dark", config_parameter=PREFIX + "dark_view")
    twp_dark_text = fields.Char("Text, dark", config_parameter=PREFIX + "dark_text")

    twp_dark_enabled = fields.Boolean(
        "Let users switch to dark mode", config_parameter=PREFIX + "dark_enabled"
    )
    twp_dark_default = fields.Selection(
        [("light", "Light"), ("dark", "Dark"), ("device", "Follow the device")],
        string="Default for new users",
        config_parameter=PREFIX + "dark_default",
        default="light",
    )

    # Typography and shape. Fonts are handled in set_values: they download.
    twp_font_body = fields.Char("Body font")
    twp_font_head = fields.Char("Heading font")
    twp_font_size = fields.Selection(
        [("13", "13px"), ("14", "14px"), ("15", "15px"), ("16", "16px")],
        string="Base font size",
        config_parameter=PREFIX + "font_size",
        default="14",
    )
    # A selection, not an integer: Odoo drops an integer setting of 0.
    twp_radius = fields.Selection(
        [(str(px), f"{px}px") for px in range(0, 13)],
        string="Corner radius",
        config_parameter=PREFIX + "radius",
        default="4",
    )

    twp_density = fields.Selection(
        [("comfortable", "Comfortable"), ("compact", "Compact")],
        string="Density",
        config_parameter=PREFIX + "density",
        default="comfortable",
    )
    twp_sheet_width = fields.Selection(
        [("normal", "Normal"), ("wide", "Wide"), ("full", "Full width")],
        string="Form width",
        config_parameter=PREFIX + "sheet_width",
        default="normal",
    )

    # Login page. The images are kept as public attachments in set_values.
    twp_login_enabled = fields.Boolean(
        "Branded login page", config_parameter=PREFIX + "login_enabled"
    )
    twp_login_layout = fields.Selection(
        [("centred", "Centred card"), ("split", "Split screen")],
        string="Login layout",
        config_parameter=PREFIX + "login_layout",
        default="centred",
    )
    twp_login_bg = fields.Char("Login background colour", config_parameter=PREFIX + "login_bg")
    twp_login_heading = fields.Char("Login heading", config_parameter=PREFIX + "login_heading")
    twp_login_tagline = fields.Char("Login tagline", config_parameter=PREFIX + "login_tagline")
    twp_login_logo = fields.Image("Login logo", attachment=False, max_width=1024, max_height=1024)
    twp_login_background = fields.Image(
        "Login background image", attachment=False, max_width=2560, max_height=2560
    )

    twp_staging_marker = fields.Boolean(
        "Mark staging copies", config_parameter=PREFIX + "staging_marker"
    )
    twp_staging_color = fields.Char("Staging colour", config_parameter=PREFIX + "staging_color")

    # Explain why a saved colour may not be what the admin sees right now.
    twp_viewing_dark = fields.Boolean(compute="_compute_twp_viewing")
    twp_is_staging_copy = fields.Boolean(compute="_compute_twp_viewing")

    def _compute_twp_viewing(self):
        dark = bool(request) and self.env["ir.http"].color_scheme() == "dark"
        neutralized = bool(
            self.env["ir.config_parameter"].sudo().get_param("database.is_neutralized")
        )
        for settings in self:
            settings.twp_viewing_dark = dark
            settings.twp_is_staging_copy = neutralized

    @api.model
    def get_values(self):
        res = super().get_values()
        Theme = self.env["twp.theme"]
        res["twp_font_body"] = Theme._param("font_body") or False
        res["twp_font_head"] = Theme._param("font_head") or False
        res["twp_login_logo"] = Theme._login_image("logo").datas or False
        res["twp_login_background"] = Theme._login_image("background").datas or False
        return res

    def set_values(self):
        for name in CHECKED_COLORS:
            value = (self[name] or "").strip()
            if value and not is_hex(value):
                raise UserError(
                    _("%(field)s must be a colour like #1F5F8B.", field=self._fields[name].string)
                )
        super().set_values()
        Theme = self.env["twp.theme"]
        Theme._set_font("font_body", self.twp_font_body)
        Theme._set_font("font_head", self.twp_font_head)
        Theme._set_login_image("logo", self.twp_login_logo)
        Theme._set_login_image("background", self.twp_login_background)
        Theme._regenerate()

    @api.model
    def _twp_look_fields(self):
        """Extended by the bridge modules that add settings to the look."""
        return list(LOOK_FIELDS)

    def action_twp_export_look(self):
        return {"type": "ir.actions.act_url", "url": "/twp_theme_settings/look", "target": "download"}

    def action_twp_import_look(self):
        return {
            "type": "ir.actions.act_window",
            "name": _("Load a look"),
            "res_model": "twp.theme.look.import",
            "view_mode": "form",
            "target": "new",
        }

    def action_twp_reset_theme(self):
        """Back to Odoo's look. Company colours are left alone."""
        ICP = self.env["ir.config_parameter"].sudo()
        keep = {PREFIX + "dark_enabled", PREFIX + "staging_marker", PREFIX + "staging_color"}
        params = ICP.search([("key", "=like", PREFIX + "%"), ("key", "not in", list(keep))])
        params.unlink()
        self.env["twp.theme"]._unlink_font_attachments()
        self.env["twp.theme"]._unlink_login_images()
        self.env["twp.theme"]._regenerate()
        return {"type": "ir.actions.client", "tag": "reload"}
