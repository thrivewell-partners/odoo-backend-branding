from odoo import api, models


class IrHttp(models.AbstractModel):
    _inherit = "ir.http"

    @api.model
    def _twp_icon_url(self, size):
        """Where a page gets the admin's icon at one size, or False for Odoo's own.

        The checksum in the URL lets the browser keep it for good, and a new
        icon is a new URL.
        """
        icon = self.env["twp.debrand"].sudo()._icon()
        if not icon:
            return False
        return f"/twp_debrand/icon/{size}?unique={(icon.checksum or '')[:8]}"

    @api.model
    def _twp_debrand_info(self):
        """What the client needs to drop Odoo's name, read on every page load
        so a switch takes effect without an upgrade."""
        Debrand = self.env["twp.debrand"].sudo()
        return {
            # Blank is Odoo's own behaviour, so the client is told nothing.
            "app_name": self.env["ir.config_parameter"].sudo().get_param("web.web_app_name") or False,
            "icon": self._twp_icon_url(192),
            "user_menu": Debrand._on("user_menu"),
            "support_url": Debrand._param("support_url") or False,
        }

    def session_info(self):
        info = super().session_info()
        debrand = info["twp_debrand"] = self._twp_debrand_info()
        # The user menu's Help item opens session.support_url.
        if debrand["user_menu"] and debrand["support_url"]:
            info["support_url"] = debrand["support_url"]
        return info

    @api.model
    def get_frontend_session_info(self):
        info = super().get_frontend_session_info()
        info["twp_debrand"] = self._twp_debrand_info()
        return info
