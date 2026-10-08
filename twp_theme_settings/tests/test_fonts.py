"""Proof 6: the server can fetch a Google Font and serve it itself.

Needs outbound HTTPS to fonts.googleapis.com and fonts.gstatic.com, so it is
tagged separately: run it with --test-tags /twp_theme_settings:TestFontDownload
or the tag twp_network.
"""

from odoo.exceptions import UserError
from odoo.tests import TransactionCase, tagged

from .common import ThemeTestMixin


@tagged("post_install", "-at_install", "-standard", "twp_network")
class TestFontDownload(ThemeTestMixin, TransactionCase):
    def test_download_store_and_reference(self):
        Theme = self.env["twp.theme"]
        Theme._set_font("font_body", "Inter")
        css_id = Theme._param("font_body_css_id")
        self.assertTrue(css_id)
        css_attachment = self.env["ir.attachment"].browse(int(css_id))
        css = css_attachment.raw.decode()
        self.assertIn("@font-face", css)
        self.assertNotIn("fonts.gstatic.com", css, "font files must be served locally")
        self.assertIn("/web/content/", css)
        files = self.env["ir.attachment"].search([("original_id", "=", css_attachment.id)])
        self.assertTrue(files)
        self.assertTrue(all(files.mapped("public")))
        Theme._regenerate()
        light = self.env["ir.attachment"].search([("url", "=", self.LIGHT_URL)]).raw.decode()
        self.assertIn('$o-system-fonts: ("Inter"', light)
        self.assertIn("@font-face", light)

    def test_same_font_twice_downloads_once(self):
        Theme = self.env["twp.theme"]
        Theme._set_font("font_body", "Lato")
        Theme._set_font("font_head", "Lato")
        self.assertEqual(Theme._param("font_body_css_id"), Theme._param("font_head_css_id"))

    def test_changing_font_removes_old_files(self):
        Theme = self.env["twp.theme"]
        Theme._set_font("font_body", "Lato")
        old = int(Theme._param("font_body_css_id"))
        Theme._set_font("font_body", "Roboto")
        self.assertFalse(self.env["ir.attachment"].search(
            ["|", ("id", "=", old), ("original_id", "=", old)]
        ))

    def test_unknown_font_is_refused(self):
        with self.assertRaises(UserError):
            self.env["twp.theme"]._set_font("font_body", "Notarealfontxyz")
        self.assertFalse(self.env["twp.theme"]._param("font_body"))

    def test_bad_name_never_leaves_the_server(self):
        with self.assertRaises(UserError):
            self.env["twp.theme"]._set_font("font_body", "Inter&subset=x")
