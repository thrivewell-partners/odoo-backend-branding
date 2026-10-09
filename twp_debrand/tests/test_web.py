import base64
import io
import json
from unittest.mock import patch

from PIL import Image

from odoo.tests import HttpCase, tagged
from odoo.tools import config

from odoo.addons.twp_debrand.models.twp_debrand import PREFIX

APP = "Northfield"
ODOO_BUY = "https://www.odoo.com/buy"


def png(color, size=(40, 20)):
    buffer = io.BytesIO()
    Image.new("RGB", size, color).save(buffer, "PNG")
    return base64.b64encode(buffer.getvalue())


@tagged("post_install", "-at_install", "twp_debrand")
class TestWeb(HttpCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.ICP = cls.env["ir.config_parameter"].sudo()
        # Start from Odoo's own behaviour; each test turns on what it checks.
        cls.ICP.search([("key", "=like", PREFIX + "%")]).unlink()
        cls.env["twp.debrand"]._unlink_icon()
        cls.ICP.set_param("web.web_app_name", False)

    def set(self, **params):
        for key, value in params.items():
            self.ICP.set_param(PREFIX + key, value)

    def name_app(self, name):
        self.ICP.set_param("web.web_app_name", name)

    def set_icon(self, size=(64, 64)):
        self.env["twp.debrand"]._set_icon(png("red", size))
        return self.env["twp.debrand"]._icon()

    def backend(self):
        self.authenticate("admin", "admin")
        response = self.url_open("/odoo")
        self.assertEqual(response.status_code, 200)
        return response.text

    def login_page(self, list_db=True):
        """Odoo's own login page.

        Website replaces the login layout with its own page (title, no
        footer), and so does the Backend Theme when its login page is on. Both
        are turned off here so the page is Odoo's whatever is installed.
        Odoo shows "Manage Databases" only when the server lists databases,
        which containers often turn off, so that is set for the request.
        """
        # By key, so a website's own copy of the view goes too.
        self.env["ir.ui.view"].search([("key", "=", "website.login_layout")]).write({"active": False})
        self.ICP.set_param("twp_theme_settings.login_enabled", False)
        with patch.dict(config._runtime_options, {"list_db": list_db}):
            response = self.url_open("/web/login")
        self.assertEqual(response.status_code, 200)
        self.assertIn("oe_login_form", response.text)
        return response.text

    # Tab title

    def test_backend_title(self):
        self.assertIn("<title>Odoo</title>", self.backend(), "blank keeps Odoo's title")
        self.name_app(APP)
        self.assertIn(f"<title>{APP}</title>", self.backend())

    def test_login_title(self):
        self.assertIn("<title>Odoo</title>", self.login_page())
        self.name_app(APP)
        self.assertIn(f"<title>{APP}</title>", self.login_page())

    def test_report_title(self):
        html = self.env["ir.qweb"]._render("web.report_layout", {})
        self.assertIn("<title>Odoo Report</title>", html)
        self.name_app(APP)
        html = self.env["ir.qweb"]._render("web.report_layout", {})
        self.assertIn(f"<title>{APP} Report</title>", html)

    # Icons and colour

    def test_backend_icons_blank_are_odoos(self):
        html = self.backend()
        self.assertIn('<link type="image/x-icon" rel="shortcut icon" href="/web/static/img/favicon.ico"/>', html)
        self.assertIn('<link rel="apple-touch-icon" href="/web/static/img/odoo-icon-ios.png"/>', html)
        self.assertIn('<meta name="theme-color" content="#71639e"/>', html)

    def test_backend_icons_set(self):
        icon = self.set_icon()
        self.set(theme_color="#1F5F8B")
        html = self.backend()
        unique = icon.checksum[:8]
        self.assertIn(
            f'<link type="image/png" rel="shortcut icon" href="/twp_debrand/icon/32?unique={unique}"/>', html
        )
        self.assertIn(f'<link rel="apple-touch-icon" href="/twp_debrand/icon/180?unique={unique}"/>', html)
        self.assertIn('<meta name="theme-color" content="#1F5F8B"/>', html)
        self.assertNotIn("/web/static/img/favicon.ico", html)

    def test_login_favicon(self):
        self.assertIn('href="/web/static/img/favicon.ico"', self.login_page())
        icon = self.set_icon()
        self.assertIn(f'href="/twp_debrand/icon/32?unique={icon.checksum[:8]}"', self.login_page())

    def test_manifest_blank_is_odoos(self):
        manifest = self.url_open("/web/manifest.webmanifest").json()
        self.assertEqual(manifest["name"], "Odoo")
        self.assertEqual(manifest["theme_color"], "#714B67")
        self.assertEqual(manifest["background_color"], "#714B67")
        self.assertEqual(
            [icon["src"] for icon in manifest["icons"]],
            ["/web/static/img/odoo-icon-192x192.png", "/web/static/img/odoo-icon-512x512.png"],
        )

    def test_manifest_set(self):
        self.name_app(APP)
        icon = self.set_icon()
        self.set(theme_color="#1F5F8B")
        manifest = self.url_open("/web/manifest.webmanifest").json()
        self.assertEqual(manifest["name"], APP)
        self.assertEqual(manifest["theme_color"], "#1F5F8B")
        self.assertEqual(manifest["background_color"], "#1F5F8B")
        unique = icon.checksum[:8]
        self.assertEqual(manifest["icons"], [
            {"src": f"/twp_debrand/icon/192?unique={unique}", "sizes": "192x192", "type": "image/png"},
            {"src": f"/twp_debrand/icon/512?unique={unique}", "sizes": "512x512", "type": "image/png"},
        ])

    def test_icon_route(self):
        self.set_icon(size=(40, 20))
        for size in (32, 180, 192, 512):
            response = self.url_open(f"/twp_debrand/icon/{size}")
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.headers["Content-Type"], "image/png")
            image = Image.open(io.BytesIO(response.content))
            self.assertEqual((image.format, image.size), ("PNG", (size, size)), "square, at the asked size")
        self.assertEqual(self.url_open("/twp_debrand/icon/100").status_code, 404)

    def test_icon_route_caches(self):
        self.set_icon()
        response = self.url_open("/twp_debrand/icon/192?unique=abc")
        self.assertIn("immutable", response.headers["Cache-Control"])
        etag = response.headers["ETag"]
        again = self.url_open("/twp_debrand/icon/192", headers={"If-None-Match": etag})
        self.assertEqual(again.status_code, 304)

    def test_icon_route_unset_redirects_to_odoos(self):
        response = self.url_open("/twp_debrand/icon/192", allow_redirects=False)
        self.assertIn(response.status_code, (301, 302, 303))
        self.assertTrue(response.headers["Location"].endswith("/web/static/img/odoo-icon-192x192.png"))
        response = self.url_open("/twp_debrand/icon/32", allow_redirects=False)
        self.assertTrue(response.headers["Location"].endswith("/web/static/img/favicon.ico"))

    def test_offline_page(self):
        html = self.url_open("/odoo/offline").text
        self.assertIn('alt="Odoo logo"', html)
        self.assertIn("Odoo will load as soon as", html)
        self.name_app(APP)
        html = self.url_open("/odoo/offline").text
        self.assertNotIn("Odoo logo", html)
        self.assertIn(f"{APP} will load as soon as", html)

    # What the web client is told

    def session_info(self):
        self.authenticate("admin", "admin")
        return self.make_jsonrpc_request("/web/session/get_session_info")

    def test_session_info_blank(self):
        info = self.session_info()
        self.assertEqual(
            info["twp_debrand"], {"app_name": False, "icon": False, "user_menu": False, "support_url": False}
        )
        self.assertEqual(info["support_url"], ODOO_BUY)

    def test_session_info_set(self):
        self.name_app(APP)
        icon = self.set_icon()
        self.set(user_menu="True", support_url="https://help.example.com")
        info = self.session_info()
        self.assertEqual(info["twp_debrand"], {
            "app_name": APP,
            "icon": f"/twp_debrand/icon/192?unique={icon.checksum[:8]}",
            "user_menu": True,
            "support_url": "https://help.example.com",
        })
        self.assertEqual(info["support_url"], "https://help.example.com", "Help opens the admin's link")

    def test_support_link_needs_the_user_menu_switch(self):
        self.set(support_url="https://help.example.com")
        self.assertEqual(self.session_info()["support_url"], ODOO_BUY)

    def test_frontend_session_info(self):
        self.name_app(APP)
        html = self.login_page()
        start = html.index("odoo.__session_info__ = ") + len("odoo.__session_info__ = ")
        info = json.loads(html[start : html.index(";\n", start)])
        self.assertEqual(info["twp_debrand"]["app_name"], APP)

    # Login footer

    def test_login_footer_off_is_odoos(self):
        html = self.login_page()
        self.assertIn('<a class="border-end pe-2 me-1" href="/web/database/manager">Manage Databases</a>', html)
        self.assertIn("https://www.odoo.com?utm_source=db&amp;utm_medium=auth", html)

    def test_login_hide_powered(self):
        self.set(login_powered="True")
        html = self.login_page()
        self.assertNotIn("utm_medium=auth", html)
        self.assertIn('<a class="me-1" href="/web/database/manager">Manage Databases</a>', html,
                      "no separator left after the last link")

    def test_login_hide_databases(self):
        self.set(login_databases="True")
        html = self.login_page()
        self.assertNotIn("/web/database/manager", html)
        self.assertIn("utm_medium=auth", html)

    def test_login_hide_powered_without_database_manager_drops_the_footer(self):
        self.set(login_powered="True")
        html = self.login_page(list_db=False)
        self.assertNotIn("text-center small mt-4 pt-3 border-top", html)
        self.set(login_powered=False)
        self.assertIn("text-center small mt-4 pt-3 border-top", self.login_page(list_db=False))

    def test_login_hide_both_drops_the_footer(self):
        self.set(login_powered="True", login_databases="True")
        html = self.login_page()
        self.assertNotIn("/web/database/manager", html)
        self.assertNotIn("utm_medium=auth", html)
        self.assertNotIn("text-center small mt-4 pt-3 border-top", html)

    # "Powered by" on frontend pages

    def test_brand_promotion(self):
        # With website installed this renders website's "Create a free
        # website" variant; both end in web.brand_promotion_message.
        html = str(self.env["ir.qweb"]._render("web.brand_promotion", {}))
        self.assertIn("Powered by", html)
        self.assertIn("/web/static/img/odoo_logo_tiny.png", html)
        self.set(promotion="True")
        html = str(self.env["ir.qweb"]._render("web.brand_promotion", {}))
        self.assertNotIn("Powered by", html)
        self.assertNotIn("odoo.com", html)
        self.assertIn("o_brand_promotion", html, "the wrapper stays for the pages that style it")
