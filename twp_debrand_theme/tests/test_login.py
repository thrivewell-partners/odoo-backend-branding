from unittest.mock import patch

from odoo.tests import HttpCase, tagged
from odoo.tools import config

from odoo.addons.twp_debrand.models.twp_debrand import PREFIX

FOOTER = "o_twp_login_footer"


@tagged("post_install", "-at_install", "twp_debrand")
class TestThemeLoginFooter(HttpCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.ICP = cls.env["ir.config_parameter"].sudo()
        cls.ICP.search([("key", "=like", PREFIX + "%")]).unlink()
        # The Backend Theme's own login page, which carries its own footer.
        cls.ICP.set_param("twp_theme_settings.login_enabled", "True")

    def set(self, **params):
        for key, value in params.items():
            self.ICP.set_param(PREFIX + key, value)

    def login_page(self, list_db=True):
        # Odoo shows "Manage Databases" only when the server lists databases,
        # which containers often turn off, so that is set for the request.
        with patch.dict(config._runtime_options, {"list_db": list_db}):
            response = self.url_open("/web/login")
        self.assertEqual(response.status_code, 200)
        self.assertIn("o_twp_login", response.text, "the Backend Theme login page is the one rendered")
        return response.text

    def test_off_is_odoos_footer(self):
        html = self.login_page()
        self.assertIn(FOOTER, html)
        self.assertIn('<a class="border-end pe-2 me-1" href="/web/database/manager">Manage Databases</a>', html)
        self.assertIn("https://www.odoo.com?utm_source=db&amp;utm_medium=auth", html)

    def test_hide_powered(self):
        self.set(login_powered="True")
        html = self.login_page()
        self.assertNotIn("utm_medium=auth", html)
        self.assertIn('<a class="me-1" href="/web/database/manager">Manage Databases</a>', html)

    def test_hide_databases(self):
        self.set(login_databases="True")
        html = self.login_page()
        self.assertNotIn("/web/database/manager", html)
        self.assertIn("utm_medium=auth", html)

    def test_hide_both_drops_the_footer(self):
        self.set(login_powered="True", login_databases="True")
        html = self.login_page()
        self.assertNotIn(FOOTER, html)
        self.assertNotIn("utm_medium=auth", html)

    def test_hide_powered_without_database_manager_drops_the_footer(self):
        self.set(login_powered="True")
        self.assertNotIn(FOOTER, self.login_page(list_db=False))
