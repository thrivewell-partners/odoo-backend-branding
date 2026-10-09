from odoo import api, models

PREFIX = "twp_debrand."
ICON = "twp_debrand_icon"
# Odoo's own values, for when a setting is blank.
ODOO_NAME = "Odoo"
ODOO_THEME_COLOR = "#71639e"


class TwpDebrand(models.AbstractModel):
    _name = "twp.debrand"
    _description = "Branding settings"

    @api.model
    def _param(self, key, default=False):
        return self.env["ir.config_parameter"].sudo().get_param(PREFIX + key, default)

    @api.model
    def _on(self, key):
        """Whether the admin's switch for one surface is on."""
        return bool(self._param(key))

    @api.model
    def _switch_on(self, keys):
        ICP = self.env["ir.config_parameter"].sudo()
        for key in keys:
            ICP.set_param(PREFIX + key, "True")

    @api.model
    def _app_name(self):
        """The name that replaces "Odoo", or Odoo's when the admin left it blank.

        Odoo already keeps one for the installable app (web.web_app_name, in
        General Settings); it is the same setting here.
        """
        return self.env["ir.config_parameter"].sudo().get_param("web.web_app_name") or ODOO_NAME

    # The icon: one square image, served at every size the browser asks for.

    @api.model
    def _icon(self):
        attachment_id = self._param("icon_id")
        if not attachment_id or not attachment_id.isdigit():
            return self.env["ir.attachment"]
        attachment = self.env["ir.attachment"].sudo().browse(int(attachment_id)).exists()
        return attachment if attachment.name == ICON else self.env["ir.attachment"]

    @api.model
    def _set_icon(self, datas):
        """Keep the icon as a public attachment."""
        ICP = self.env["ir.config_parameter"].sudo()
        current = self._icon()
        if not datas:
            current.unlink()
            ICP.set_param(PREFIX + "icon_id", False)
            return
        if current and current.datas == datas:
            return
        if current:
            current.write({"datas": datas})
        else:
            current = self.env["ir.attachment"].sudo().create({
                "name": ICON,
                "type": "binary",
                "datas": datas,
                "public": True,
            })
            ICP.set_param(PREFIX + "icon_id", str(current.id))

    @api.model
    def _unlink_icon(self):
        self.env["ir.attachment"].sudo().search([("name", "=", ICON)]).unlink()

    @api.model
    def _theme_color(self):
        return self._param("theme_color") or ODOO_THEME_COLOR
