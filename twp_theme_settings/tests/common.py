from odoo.addons.twp_theme_settings.models.twp_theme import DARK_URL, LIGHT_URL, PREFIX


class ThemeTestMixin:
    LIGHT_URL = LIGHT_URL
    DARK_URL = DARK_URL

    def set_theme(self, **params):
        ICP = self.env["ir.config_parameter"].sudo()
        for key, value in params.items():
            ICP.set_param(PREFIX + key, value)
        self.env["twp.theme"]._regenerate()

    def bundle_urls(self, bundle):
        files, _external = self.env["ir.qweb"]._get_asset_content(bundle)
        return [f["url"] for f in files]

    def scss_urls(self, bundle):
        return [url for url in self.bundle_urls(bundle) if url.endswith((".scss", ".css"))]
