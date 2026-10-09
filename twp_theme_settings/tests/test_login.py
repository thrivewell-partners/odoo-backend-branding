import base64
import io

from PIL import Image

from odoo.tests import HttpCase, tagged

from .common import ThemeTestMixin


def png(color, size=(40, 20)):
    buffer = io.BytesIO()
    Image.new("RGB", size, color).save(buffer, "PNG")
    return base64.b64encode(buffer.getvalue())


@tagged("post_install", "-at_install", "twp_theme")
class TestLoginPage(ThemeTestMixin, HttpCase):
    def login_page(self):
        self.logout()
        response = self.url_open("/web/login")
        self.assertEqual(response.status_code, 200)
        return response.text

    def save(self, **values):
        self.env["res.config.settings"].create(values).execute()

    def test_off_keeps_odoos_page(self):
        self.set_theme(login_enabled=False)
        html = self.login_page()
        self.assertNotIn("o_twp_login", html)
        self.assertIn("oe_login_form", html)

    def test_centred_page_with_heading_and_colours(self):
        self.save(
            twp_login_enabled=True, twp_login_heading="Welcome to Northfield",
            twp_login_tagline="Field service, done right", twp_primary="#1F5F8B",
            twp_login_bg="#16324F",
        )
        html = self.login_page()
        self.assertIn("o_twp_login_centred", html)
        self.assertIn("Welcome to Northfield", html)
        self.assertIn("Field service, done right", html)
        self.assertIn("--btn-bg: #1F5F8B", html)
        self.assertIn("body.o_twp_login_body { background: #16324F; }", html)
        self.assertIn("oe_login_form", html, "the login form itself must still render")
        self.assertIn("/web/binary/company_logo", html, "blank logo uses the company logo")

    def test_split_page(self):
        self.save(twp_login_enabled=True, twp_login_layout="split", twp_login_heading="Hello")
        html = self.login_page()
        self.assertIn("o_twp_login_split", html)
        self.assertIn("o_twp_login_aside", html)

    def test_heading_is_escaped(self):
        self.save(twp_login_enabled=True, twp_login_heading="<script>alert(1)</script>")
        html = self.login_page()
        self.assertNotIn("<script>alert(1)</script>", html)
        self.assertIn("&lt;script&gt;", html)

    def test_images_are_public_and_replaced(self):
        self.save(twp_login_enabled=True, twp_login_logo=png("red"), twp_login_background=png("blue"))
        Theme = self.env["twp.theme"]
        logo = Theme._login_image("logo")
        self.assertTrue(logo.public)
        html = self.login_page()
        self.assertIn(f"/web/image/{logo.id}?unique=", html)
        self.assertIn(f"/web/image/{Theme._login_image('background').id}?unique=", html)
        response = self.url_open(f"/web/image/{logo.id}")
        self.assertEqual(response.status_code, 200, "anonymous visitors must see the logo")
        # Saving the same image keeps the attachment; clearing removes it.
        self.save(twp_login_enabled=True, twp_login_logo=png("red"), twp_login_background=False)
        self.assertEqual(Theme._login_image("logo"), logo)
        self.assertFalse(Theme._login_image("background"))
        self.assertFalse(
            self.env["ir.attachment"].sudo().search_count([("name", "=", "twp-login-background")])
        )

    def test_bad_background_colour_refused(self):
        with self.assertRaises(Exception):
            self.save(twp_login_enabled=True, twp_login_bg="red; } body { display:none")
