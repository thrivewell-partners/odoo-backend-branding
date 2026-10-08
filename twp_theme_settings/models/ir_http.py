from odoo import models
from odoo.http import request


class IrHttp(models.AbstractModel):
    _inherit = "ir.http"

    def color_scheme(self):
        Theme = self.env["twp.theme"]
        if not request or not Theme._dark_enabled():
            return super().color_scheme()
        user = request.env.user
        if not user or not user._is_internal():
            return super().color_scheme()
        chosen = user.sudo().res_users_settings_ids[:1].twp_color_scheme
        if chosen:
            return chosen
        default = Theme._param("dark_default", "light")
        if default == "device":
            # Chromium sends this hint once asked for it (see _post_dispatch).
            # Elsewhere the client corrects the cookie and reloads once.
            hint = request.httprequest.headers.get("Sec-CH-Prefers-Color-Scheme")
            if hint in ("light", "dark"):
                return hint
            cookie = request.httprequest.cookies.get("color_scheme")
            return cookie if cookie in ("light", "dark") else "light"
        return "dark" if default == "dark" else "light"

    def _twp_current_company(self):
        """The company the page is being rendered for.

        Switching company is a full reload that writes the cids cookie, but the
        server does not read cids when it renders the web client, so
        env.company is the user's default company. Read the cookie here.
        """
        user = request.env.user
        cids = request.httprequest.cookies.get("cids", "")
        first = cids.split("-")[0]
        if first.isdigit():
            company = user.company_ids.filtered(lambda c: c.id == int(first))
            if company:
                return company
        return user.company_id

    def webclient_rendering_context(self):
        context = super().webclient_rendering_context()
        scheme = context.get("color_scheme", "light")
        company = self._twp_current_company()
        context["twp_runtime_css"] = self.env["twp.theme"]._runtime_css(company.sudo(), scheme)
        session_info = context.get("session_info")
        if session_info is not None:
            session_info["twp_color_scheme"] = scheme
            session_info["twp_dark_enabled"] = self.env["twp.theme"]._dark_enabled()
            session_info["twp_follow_device"] = (
                self.env["twp.theme"]._param("dark_default", "light") == "device"
                and not request.env.user.sudo().res_users_settings_ids[:1].twp_color_scheme
            )
        return context

    @classmethod
    def _post_dispatch(cls, response):
        # Ask Chromium browsers to send the device's light or dark preference,
        # used when the admin's default for new users is "follow the device".
        response.headers.add("Accept-CH", "Sec-CH-Prefers-Color-Scheme")
        return super()._post_dispatch(response)
