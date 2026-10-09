from odoo.tests import TransactionCase, tagged

from odoo.addons.twp_theme_settings.models.twp_theme import PALETTE

from .common import ThemeTestMixin


@tagged("post_install", "-at_install", "twp_theme")
class TestGeneration(ThemeTestMixin, TransactionCase):
    def clear_theme(self):
        self.env["ir.config_parameter"].sudo().search(
            [("key", "=like", "twp_theme_settings.%")]
        ).unlink()

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
        self.assertNotIn("display:none", light)
        self.assertNotIn("body {", light)
        self.assertNotIn("$o-font-size-base", light)
        self.assertEqual(set(self.env["twp.theme"]._dark_palette()), set(PALETTE))

    def test_primary_and_navbar_follow_each_other(self):
        self.set_theme(navbar="#36BA87")
        light = self.attachment_text(self.LIGHT_URL)
        self.assertIn("$o-brand-primary: #36BA87 !default;", light)
        self.assertIn("$o-enterprise-action-color: #36BA87 !default;", light)
        self.set_theme(navbar="", primary="#1F5F8B")
        light = self.attachment_text(self.LIGHT_URL)
        self.assertIn("$o-navbar-background: #1F5F8B !default;", light)
        self.assertIn("$o-brand-odoo: #1F5F8B !default;", light)

    def test_sheet_colour_rebuilds_the_gray_scale(self):
        self.set_theme(view="#FFF8EE")
        light = self.attachment_text(self.LIGHT_URL)
        self.assertIn("$o-white: #FFF8EE !default;", light)
        self.assertIn("$o-gray-300:", light)
        self.assertNotIn("$o-main-text-color", light, "text stays Odoo's on a light sheet")
        self.assertNotIn("$o-black", light)

    def test_dark_sheet_gets_light_text(self):
        self.set_theme(view="#357231")
        light = self.attachment_text(self.LIGHT_URL)
        self.assertIn("$o-main-text-color: #E5E7EB !default;", light)
        self.assertIn("$o-black: #FFFFFF !default;", light)

    def test_links_stay_readable_on_the_sheet(self):
        from odoo.addons.twp_theme_settings.models.colors import contrast
        import re
        self.set_theme(navbar="#36BA87", view="#357231")
        light = self.attachment_text(self.LIGHT_URL)
        link = re.search(r"\$o-main-link-color: (#[0-9A-F]{6})", light).group(1)
        self.assertGreaterEqual(contrast(link, "#357231"), 4.5)
        self.assertIn("$color-contrast-dark: #111827 !default;", light)
        # Odoo would write the primary button's text in the sheet colour.
        self.assertIn('("primary": (background: #36BA87, border: #36BA87, color: #111827', light)

    def state_text(self, scss):
        import re
        found = re.search(r"\$o-theme-text-colors: \(([^)]*)\)", scss)
        if not found:
            return None
        return dict(re.findall(r'"(\w+)": (#[0-9A-F]{6})', found.group(1)))

    def test_dark_state_text_reads_on_the_sheet(self):
        """text-success, list row decorations and remaining days are Odoo's
        fixed dark shades unless the dark file replaces them."""
        from odoo.addons.twp_theme_settings.models.colors import DARK_INK, contrast, ink
        self.clear_theme()
        self.set_theme(success="#2E7D4F", dark_view="#262A33")
        Theme = self.env["twp.theme"]
        dark_palette = Theme._dark_palette()
        dark = self.attachment_text(self.DARK_URL)
        text = self.state_text(dark)
        self.assertEqual(set(text), {"success", "info", "warning", "danger"})
        for key, value in text.items():
            self.assertGreaterEqual(contrast(value, "#262A33"), 4.5, key)
        self.assertIn(f"$o-navbar-badge-color: {ink(dark_palette['success'])} !default;", dark)
        self.assertEqual(ink(dark_palette["success"]), DARK_INK, "white on a lightened green")
        self.assertIn("$o-navbar-badge-text-shadow: none !default;", dark)
        code = dark.split("$o-main-code-color: ")[1][:7]
        self.assertGreaterEqual(contrast(code, "#262A33"), 4.5)

    def test_light_state_text_is_odoos_until_changed(self):
        self.clear_theme()
        self.set_theme(primary="#1F5F8B")
        light = self.attachment_text(self.LIGHT_URL)
        self.assertIsNone(self.state_text(light), "Odoo's tuned shades stay")
        self.assertNotIn("$o-navbar-badge-color", light)
        self.assertNotIn("$o-main-code-color", light)

        self.set_theme(success="#7CD992")
        text = self.state_text(self.attachment_text(self.LIGHT_URL))
        self.assertEqual(text["info"], "#0180A5", "colours left alone keep Odoo's shade")
        self.assertNotEqual(text["success"], "#7CD992", "a pale green is darkened to read on white")
        light = self.attachment_text(self.LIGHT_URL)
        self.assertIn("$o-navbar-badge-color: #111827 !default;", light)

    def test_density_and_width(self):
        self.set_theme(density="compact", sheet_width="wide")
        light = self.attachment_text(self.LIGHT_URL)
        self.assertIn("$o-table-cell-padding-y-sm: .25rem !default;", light)
        self.assertIn("$o-form-spacing-unit: 3px !default;", light)
        self.assertIn("$o-form-view-sheet-max-width: 1800px !default;", light)
        self.assertNotIn("$o-form-renderer-max-width", light)
        self.set_theme(density="comfortable", sheet_width="normal")
        light = self.attachment_text(self.LIGHT_URL)
        self.assertNotIn("$o-form-spacing-unit", light)
        self.assertNotIn("sheet-max-width", light)

    def test_settings_reject_bad_colour(self):
        settings = self.env["res.config.settings"].create({"twp_primary": "blue"})
        with self.assertRaises(Exception):
            settings.execute()
