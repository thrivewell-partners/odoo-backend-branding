"""Proofs 2 and 4, server side: the page a user actually gets."""

from odoo.tests import HttpCase, new_test_user, tagged

from .common import ThemeTestMixin

PASSWORD = "twp-theme-test-Pw1"


@tagged("post_install", "-at_install", "twp_theme")
class TestWebclient(ThemeTestMixin, HttpCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company_a = cls.env.company
        cls.company_b = cls.env["res.company"].create({
            "name": "TWP Test Services",
            "twp_navbar_color": "#3B2F5C",
            "twp_accent_color": "#6B4FA0",
        })
        cls.user = new_test_user(
            cls.env, login="twp_theme_user", password=PASSWORD,
            groups="base.group_user",
            company_id=cls.company_a.id,
            company_ids=[(6, 0, (cls.company_a | cls.company_b).ids)],
        )
        ICP = cls.env["ir.config_parameter"].sudo()
        ICP.set_param("twp_theme_settings.dark_enabled", "True")
        ICP.set_param("twp_theme_settings.staging_marker", "True")
        ICP.set_param("twp_theme_settings.dark_default", "light")
        # Oduflow environments are neutralized copies, where the staging marker
        # rightly overrides company colours. Tests that want it turn it back on.
        ICP.set_param("database.is_neutralized", False)

    def page(self, cookies=None):
        self.authenticate("twp_theme_user", PASSWORD)
        if cookies:
            for name, value in cookies.items():
                self.opener.cookies.set(name, value)
        response = self.url_open("/odoo")
        self.assertEqual(response.status_code, 200)
        return response.text

    def set_user_scheme(self, scheme):
        settings = self.env["res.users.settings"]._find_or_create_for_user(self.user)
        settings.twp_color_scheme = scheme

    def test_light_by_default(self):
        html = self.page()
        self.assertNotIn("web.assets_web_dark", html)

    def test_user_choice_dark_serves_dark_bundle(self):
        self.set_user_scheme("dark")
        html = self.page()
        self.assertIn("web.assets_web_dark", html)
        self.assertIn('"twp_color_scheme": "dark"', html)

    def test_admin_switch_off_forces_light(self):
        self.set_user_scheme("dark")
        self.env["ir.config_parameter"].sudo().set_param("twp_theme_settings.dark_enabled", False)
        html = self.page()
        self.assertNotIn("web.assets_web_dark", html)

    def test_admin_default_dark_for_users_who_never_chose(self):
        self.env["ir.config_parameter"].sudo().set_param("twp_theme_settings.dark_default", "dark")
        html = self.page()
        self.assertIn("web.assets_web_dark", html)

    def test_company_colours_follow_switched_company(self):
        html = self.page()
        self.assertNotIn("#3B2F5C", html, "company B's colour shown while on company A")
        html = self.page(cookies={"cids": f"{self.company_b.id}-{self.company_a.id}"})
        self.assertIn('id="twp_runtime_css"', html)
        self.assertIn("#3B2F5C", html)
        self.assertIn("--btn-bg:#6B4FA0", html)

    def test_company_dark_colour_derived_when_blank(self):
        self.set_user_scheme("dark")
        html = self.page(cookies={"cids": str(self.company_b.id)})
        self.assertNotIn("background:#3B2F5C", html, "light navbar used in dark mode")
        self.assertIn("twp_runtime_css", html)

    def test_cids_for_a_foreign_company_is_ignored(self):
        other = self.env["res.company"].create({"name": "Not Mine", "twp_navbar_color": "#ABCDEF"})
        html = self.page(cookies={"cids": str(other.id)})
        self.assertNotIn("#ABCDEF", html)

    def test_staging_marker_on_neutralized_copy(self):
        self.env["ir.config_parameter"].sudo().set_param("database.is_neutralized", True)
        self.env["ir.config_parameter"].sudo().set_param("twp_theme_settings.staging_color", "#B7472A")
        html = self.page()
        self.assertIn("#B7472A", html)
        self.assertIn("STAGING", html)

    def test_staging_marker_can_be_turned_off(self):
        ICP = self.env["ir.config_parameter"].sudo()
        ICP.set_param("database.is_neutralized", True)
        ICP.set_param("twp_theme_settings.staging_marker", False)
        html = self.page()
        self.assertNotIn("STAGING", html)

    def test_navbar_logo_per_company(self):
        png = (
            "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg=="
        )
        self.company_b.twp_navbar_logo = png
        html = self.page()
        entry = r'"id": %d, "name": "%s"[^}]*"twp_navbar_logo": '
        self.assertRegex(html, entry % (self.company_b.id, self.company_b.name) + r'"\d+"')
        self.assertRegex(html, entry % (self.company_a.id, self.company_a.name) + "false")
        url = f"/web/image/res.company/{self.company_b.id}/twp_navbar_logo"
        response = self.url_open(url)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.headers["Content-Type"].startswith("image/"))
