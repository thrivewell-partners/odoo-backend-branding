"""Proof 1: the theme compiles into the backend bundles and nowhere else."""

import logging

from odoo.modules import Manifest
from odoo.tests import TransactionCase, tagged

from .common import ThemeTestMixin

_logger = logging.getLogger(__name__)

BACKEND_BUNDLES = ("web.assets_backend", "web.assets_backend_lazy")
DARK_BUNDLES = ("web.assets_web_dark", "web.assets_backend_lazy_dark")
# Bundles a visitor, a portal user, a printed report or the login page loads.
MUST_NOT_CHANGE = (
    "web.assets_frontend",
    "web.assets_frontend_minimal",
    "web.assets_frontend_lazy",
    "web.report_assets_common",
    "web.report_assets_pdf",
)


@tagged("post_install", "-at_install", "twp_theme")
class TestBundles(ThemeTestMixin, TransactionCase):
    def all_bundle_names(self):
        installed = self.env["ir.module.module"].search([("state", "=", "installed")]).mapped("name")
        names = set(self.env["ir.asset"].search([]).mapped("bundle"))
        for module in installed:
            manifest = Manifest.for_addon(module, display_warning=False)
            if manifest:
                names.update(manifest.get("assets", {}).keys())
        return sorted(names)

    def test_backend_bundles_put_theme_first(self):
        for bundle in BACKEND_BUNDLES:
            urls = self.scss_urls(bundle)
            self.assertEqual(urls[0], self.LIGHT_URL, f"{bundle} does not start with the theme")

    def test_dark_bundles_put_dark_theme_first(self):
        for bundle in DARK_BUNDLES:
            urls = self.scss_urls(bundle)
            self.assertEqual(urls[0], self.DARK_URL, f"{bundle} does not start with the dark theme")
            self.assertIn(self.LIGHT_URL, urls, f"{bundle} lost the light theme (fonts, shape)")

    def test_frontend_bundles_untouched(self):
        for bundle in MUST_NOT_CHANGE:
            urls = self.bundle_urls(bundle)
            self.assertNotIn(self.LIGHT_URL, urls, bundle)
            self.assertNotIn(self.DARK_URL, urls, bundle)

    def test_report_which_bundles_carry_the_theme(self):
        """Not an assertion: logs the full list so a run shows the blast radius."""
        carrying = []
        for bundle in self.all_bundle_names():
            if bundle.startswith("web._") or ".tests" in bundle or "unit_tests" in bundle:
                continue
            try:
                urls = self.bundle_urls(bundle)
            except Exception as e:  # noqa: BLE001 - a bundle we cannot resolve is reported, not fatal
                _logger.info("TWP bundle %s could not be resolved: %s", bundle, e)
                continue
            if self.LIGHT_URL in urls or self.DARK_URL in urls:
                carrying.append(bundle)
        _logger.info("TWP bundles carrying the theme: %s", ", ".join(carrying))
        frontend_like = [b for b in carrying if "frontend" in b or "website" in b or "report" in b
                         or "pos" in b or "portal" in b or "login" in b]
        self.assertFalse(frontend_like, f"Theme leaked into: {frontend_like}")

    def test_frontend_version_unchanged_by_theme_change(self):
        Qweb = self.env["ir.qweb"]
        before = {b: Qweb._get_asset_bundle(b, js=False).get_version("css") for b in MUST_NOT_CHANGE}
        backend_before = Qweb._get_asset_bundle("web.assets_backend", js=False).get_version("css")
        self.set_theme(primary="#1F5F8B", navbar="#16324F")
        after = {b: Qweb._get_asset_bundle(b, js=False).get_version("css") for b in MUST_NOT_CHANGE}
        backend_after = Qweb._get_asset_bundle("web.assets_backend", js=False).get_version("css")
        self.assertEqual(before, after)
        self.assertNotEqual(backend_before, backend_after, "Saving the theme did not change the backend bundle")


@tagged("post_install", "-at_install", "twp_theme", "twp_compile")
class TestCompile(ThemeTestMixin, TransactionCase):
    """Compiles real bundles with a full theme. Slow: tens of seconds each."""

    def compile(self, bundle):
        assets = self.env["ir.qweb"]._get_asset_bundle(bundle, js=False)
        css = assets.preprocess_css()
        self.assertFalse(assets.css_errors, f"{bundle}: {assets.css_errors}")
        return css

    def test_full_theme_compiles_light_and_dark(self):
        self.set_theme(
            primary="#1F5F8B", navbar="#F4F4F4", success="#2E7D4F", info="#2B7A9B",
            warning="#B7791F", danger="#B03A2E", bg="#F3F4F6", view="#FFFFFF", text="#1F2933",
            dark_navbar="#0E1C2E", font_size="15", radius="0",
        )
        css = self.compile("web.assets_backend")
        self.assertIn("#1f5f8b", css.lower(), "primary colour missing from compiled CSS")
        dark = self.compile("web.assets_web_dark")
        self.assertIn("#0e1c2e", dark.lower(), "custom dark navbar missing from compiled dark CSS")
        self.compile("web.assets_backend_lazy")
        self.compile("web.assets_backend_lazy_dark")

    def test_layout_settings_compile(self):
        self.set_theme(density="compact", sheet_width="full")
        css = self.compile("web.assets_backend")
        self.assertIn("max-width: 100vw", css, "full-width sheet missing from compiled CSS")
        self.assertIn("min-width: 560px", css, "property editor lost its width")
        self.compile("web.assets_web_dark")
