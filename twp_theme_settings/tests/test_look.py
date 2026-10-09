import base64
import json

from odoo.exceptions import UserError
from odoo.tests import HttpCase, new_test_user, tagged

from odoo.addons.twp_theme_settings.models.twp_theme import PREFIX

from .common import ThemeTestMixin
from .test_login import png

LOOK = {
    "twp_primary": "#1F5F8B",
    "twp_navbar": "#16324F",
    "twp_dark_primary": "#7FB2D9",
    "twp_font_size": "15",
    "twp_radius": "0",
    "twp_density": "compact",
    "twp_sheet_width": "wide",
    "twp_dark_enabled": True,
    "twp_dark_default": "device",
    "twp_login_enabled": True,
    "twp_login_layout": "split",
    "twp_login_heading": "Welcome to Northfield",
    "twp_login_bg": "#16324F",
}


@tagged("post_install", "-at_install", "twp_theme")
class TestLook(ThemeTestMixin, HttpCase):
    def setUp(self):
        super().setUp()
        # Start from Odoo's look, whatever the database had saved.
        self.reset()

    def save(self, **values):
        self.env["res.config.settings"].create(values).execute()

    def params(self):
        ICP = self.env["ir.config_parameter"].sudo()
        rows = ICP.search([("key", "=like", PREFIX + "%")])
        return {row.key.removeprefix(PREFIX): row.value for row in rows if not row.key.endswith("_id")}

    def to_file(self, look):
        return json.dumps(look).encode()

    def reset(self):
        self.env["res.config.settings"].create({}).action_twp_reset_theme()

    def test_export_lists_every_setting(self):
        self.save(**LOOK, twp_login_logo=png("red"), twp_staging_marker=True, twp_staging_color="#123456")
        look = self.env["twp.theme"]._export_look()
        self.assertEqual((look["format"], look["version"]), ("twp-backend-look", 1))
        settings = look["settings"]
        self.assertEqual(settings["primary"], "#1F5F8B")
        self.assertEqual(settings["radius"], "0")
        self.assertIs(settings["dark_enabled"], True)
        self.assertIsNone(settings["success"], "a blank colour is null")
        self.assertIsNone(settings["login_background"])
        self.assertTrue(base64.b64decode(settings["login_logo"]))
        self.assertNotIn("staging_marker", settings)
        self.assertNotIn("staging_color", settings)
        json.dumps(look)

    def test_round_trip(self):
        self.save(**LOOK, twp_login_logo=png("red"))
        before = self.params()
        logo = self.env["twp.theme"]._login_image("logo").checksum
        raw = self.to_file(self.env["twp.theme"]._export_look())
        self.reset()
        self.assertNotEqual(self.params(), before)
        values, ignored = self.env["twp.theme"]._read_look(raw)
        self.env["twp.theme"]._apply_look(values)
        self.assertEqual(self.params(), before)
        self.assertEqual(self.env["twp.theme"]._login_image("logo").checksum, logo)
        self.assertIn("$o-brand-primary: #1F5F8B", self.env["twp.theme"]._build_light_scss())
        self.assertFalse(ignored)

    def test_blank_settings_return_to_odoo(self):
        self.save(**LOOK)
        look = self.env["twp.theme"]._export_look()
        for key in look["settings"]:
            look["settings"][key] = None
        look["settings"]["primary"] = "#aa3311"
        values, _ignored = self.env["twp.theme"]._read_look(self.to_file(look))
        self.env["twp.theme"]._apply_look(values)
        params = self.params()
        self.assertEqual(params.get("primary"), "#AA3311")
        for key in ("navbar", "dark_primary", "density", "login_heading", "login_enabled"):
            self.assertNotIn(key, params)

    def test_staging_and_companies_kept(self):
        company = self.env.company
        company.write({"twp_navbar_color": "#3B2F5C", "twp_navbar_logo": png("blue")})
        self.save(twp_staging_marker=True, twp_staging_color="#123456")
        look = self.env["twp.theme"]._export_look()
        values, _ignored = self.env["twp.theme"]._read_look(self.to_file(look))
        self.env["twp.theme"]._apply_look(values)
        self.assertEqual(self.params().get("staging_color"), "#123456")
        self.assertEqual(company.twp_navbar_color, "#3B2F5C")
        self.assertTrue(company.twp_navbar_logo)

    def test_bad_files_refused(self):
        good = self.env["twp.theme"]._export_look()
        bad = {
            "not json": b"\x89PNG not a look",
            "other json": json.dumps({"hello": 1}).encode(),
            "newer": self.to_file({**good, "version": 2}),
            "no settings": self.to_file({**good, "settings": []}),
            "bad colour": self.to_file({**good, "settings": {**good["settings"], "primary": "#12"}}),
            "bad choice": self.to_file({**good, "settings": {**good["settings"], "density": "tiny"}}),
            "bad switch": self.to_file({**good, "settings": {**good["settings"], "dark_enabled": "yes"}}),
            "bad font": self.to_file({**good, "settings": {**good["settings"], "font_body": "<b>Inter"}}),
            "bad image": self.to_file({**good, "settings": {**good["settings"], "login_logo": "not base64!"}}),
        }
        for name, raw in bad.items():
            with self.subTest(name), self.assertRaises(UserError):
                self.env["twp.theme"]._read_look(raw)

    def test_unknown_settings_ignored(self):
        look = self.env["twp.theme"]._export_look()
        look["settings"]["sparkles"] = True
        values, ignored = self.env["twp.theme"]._read_look(self.to_file(look))
        self.assertEqual(ignored, ["sparkles"])
        self.assertNotIn("twp_sparkles", values)

    def test_wizard(self):
        self.save(**LOOK)
        raw = self.to_file(self.env["twp.theme"]._export_look())
        self.reset()
        wizard = self.env["twp.theme.look.import"].create({"look_file": base64.b64encode(raw)})
        self.assertFalse(wizard.look_error)
        self.assertIn("primary #1F5F8B", wizard.summary)
        self.assertIn("Branded login page: on.", wizard.summary)
        self.assertIn("Text 15px, corners 0px, compact rows, wide forms.", wizard.summary)
        self.assertEqual(wizard.action_load()["tag"], "reload")
        self.assertEqual(self.params().get("login_heading"), "Welcome to Northfield")

        broken = self.env["twp.theme.look.import"].create({"look_file": base64.b64encode(b"{}")})
        self.assertTrue(broken.look_error)
        with self.assertRaises(UserError):
            broken.action_load()

    def test_download(self):
        self.save(twp_primary="#1F5F8B")
        self.authenticate("admin", "admin")
        response = self.url_open("/twp_theme_settings/look")
        self.assertEqual(response.status_code, 200)
        self.assertIn("attachment", response.headers["Content-Disposition"])
        self.assertEqual(response.json()["settings"]["primary"], "#1F5F8B")

        new_test_user(self.env, login="look_user", password="look_user_pw1", groups="base.group_user")
        self.authenticate("look_user", "look_user_pw1")
        self.assertEqual(self.url_open("/twp_theme_settings/look").status_code, 403)
