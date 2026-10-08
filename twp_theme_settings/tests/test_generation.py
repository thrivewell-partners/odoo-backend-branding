from odoo.tests import TransactionCase, tagged

from odoo.addons.twp_theme_settings.models.twp_theme import PALETTE

from .common import ThemeTestMixin


@tagged("post_install", "-at_install", "twp_theme")
class TestGeneration(ThemeTestMixin, TransactionCase):
    def attachment_text(self, url):
        return self.env["ir.attachment"].sudo().search([("url", "=", url)]).raw.decode()

    def test_blank_theme_changes_nothing(self):
        self.env["ir.config_parameter"].sudo().search(
            [("key", "=like", "twp_theme_settings.%")]
        ).unlink()
        self.env["twp.theme"]._regenerate()
        light = self.attachment_text(self.LIGHT_URL)
        self.assertNotIn("$o-", light, "a blank theme should leave Odoo's values alone")

    def test_light_values_are_written(self):
        self.set_theme(primary="#1f5f8b", navbar="#16324F", radius="6", font_size="15")
        light = self.attachment_text(self.LIGHT_URL)
        self.assertIn("$o-brand-primary: #1F5F8B !default;", light)
        self.assertIn("$o-navbar-background: #16324F !default;", light)
        self.assertIn("$o-border-radius: 0.3750rem !default;", light)
        self.assertIn("$o-font-size-base: 0.9375rem !default;", light)

    def test_dark_file_covers_every_colour(self):
        """Anything the dark file leaves out falls through to the light value."""
        self.set_theme(view="#FFFFFF", text="#1F2933", primary="#1F5F8B")
        dark = self.attachment_text(self.DARK_URL)
        for var in ("$o-brand-primary", "$o-navbar-background", "$o-success", "$o-info",
                    "$o-warning", "$o-danger", "$o-webclient-background-color",
                    "$o-view-background-color", "$o-main-text-color"):
            self.assertIn(var + ":", dark)
        self.assertNotIn("$o-view-background-color: #FFFFFF", dark)

    def test_custom_dark_colour_beats_derived(self):
        self.set_theme(navbar="#16324F", dark_navbar="#0E1C2E")
        palette = self.env["twp.theme"]._dark_palette()
        self.assertEqual(palette["navbar"], "#0E1C2E")
        self.set_theme(dark_navbar="")
        self.assertNotEqual(self.env["twp.theme"]._dark_palette()["navbar"], "#0E1C2E")

    def test_invalid_values_never_reach_scss(self):
        self.set_theme(primary="red; } body { display:none", font_size="99", radius="x")
        light = self.attachment_text(self.LIGHT_URL)
        self.assertNotIn("display", light)
        self.assertNotIn("font-size", light)
        self.assertEqual(set(self.env["twp.theme"]._dark_palette()), set(PALETTE))

    def test_settings_reject_bad_colour(self):
        settings = self.env["res.config.settings"].create({"twp_primary": "blue"})
        with self.assertRaises(Exception):
            settings.execute()
