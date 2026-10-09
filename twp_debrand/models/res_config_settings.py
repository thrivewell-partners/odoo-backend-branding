from odoo import _, api, fields, models
from odoo.exceptions import UserError

from .twp_debrand import PREFIX

HEX = "0123456789abcdefABCDEF"


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    # App name is Odoo's own web_app_name (web), shown again under Branding.

    # Icons. The image is kept as a public attachment in set_values.
    twp_debrand_icon = fields.Image("Icon", attachment=False, max_width=512, max_height=512)
    twp_debrand_theme_color = fields.Char(
        "Browser colour", config_parameter=PREFIX + "theme_color"
    )

    twp_debrand_user_menu = fields.Boolean(
        "Hide Odoo's user menu items", config_parameter=PREFIX + "user_menu"
    )
    twp_debrand_support_url = fields.Char(
        "Support link", config_parameter=PREFIX + "support_url"
    )

    twp_debrand_login_powered = fields.Boolean(
        'Hide "Powered by Odoo" on the login page', config_parameter=PREFIX + "login_powered"
    )
    twp_debrand_login_databases = fields.Boolean(
        'Hide "Manage Databases"', config_parameter=PREFIX + "login_databases"
    )

    twp_debrand_promotion = fields.Boolean(
        'Hide "Powered by Odoo" on the portal and website', config_parameter=PREFIX + "promotion"
    )

    twp_debrand_settings = fields.Boolean(
        "Hide the edition and Enterprise upsells", config_parameter=PREFIX + "settings"
    )

    @api.model
    def get_values(self):
        res = super().get_values()
        res["twp_debrand_icon"] = self.env["twp.debrand"]._icon().datas or False
        return res

    def set_values(self):
        color = (self.twp_debrand_theme_color or "").strip()
        if color and not (len(color) == 7 and color[0] == "#" and all(c in HEX for c in color[1:])):
            raise UserError(_("Browser colour must be a colour like #1F5F8B."))
        url = (self.twp_debrand_support_url or "").strip()
        if url and not url.startswith(("https://", "http://", "mailto:")):
            raise UserError(_("Support link must start with https://, http:// or mailto:."))
        super().set_values()
        self.env["twp.debrand"]._set_icon(self.twp_debrand_icon)
