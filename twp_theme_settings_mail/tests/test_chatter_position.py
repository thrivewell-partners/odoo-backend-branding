import json

from odoo.tests import HttpCase, tagged

from odoo.addons.twp_theme_settings.models.twp_theme import PREFIX


@tagged("post_install", "-at_install", "twp_theme")
class TestChatterPosition(HttpCase):
    def position_in_session(self):
        self.authenticate("admin", "admin")
        response = self.url_open("/odoo")
        self.assertEqual(response.status_code, 200)
        marker = '"twp_chatter_position": "'
        text = response.text
        start = text.index(marker) + len(marker)
        return text[start : text.index('"', start)]

    def test_default_is_odoo(self):
        self.env["ir.config_parameter"].sudo().set_param(PREFIX + "chatter_position", False)
        self.assertEqual(self.position_in_session(), "auto")

    def test_setting_reaches_the_client(self):
        settings = self.env["res.config.settings"].create({"twp_chatter_position": "side"})
        settings.execute()
        self.assertEqual(self.position_in_session(), "side")

    def test_unknown_value_falls_back(self):
        self.env["ir.config_parameter"].sudo().set_param(PREFIX + "chatter_position", "nonsense")
        self.assertEqual(self.position_in_session(), "auto")

    def test_position_travels_with_the_look(self):
        self.env["res.config.settings"].create({"twp_chatter_position": "side"}).execute()
        look = self.env["twp.theme"]._export_look()
        self.assertEqual(look["settings"]["chatter_position"], "side")
        look["settings"]["chatter_position"] = "bottom"
        values, ignored = self.env["twp.theme"]._read_look(json.dumps(look).encode())
        self.assertFalse(ignored)
        self.env["twp.theme"]._apply_look(values)
        self.assertEqual(self.env["ir.config_parameter"].sudo().get_param(PREFIX + "chatter_position"), "bottom")
