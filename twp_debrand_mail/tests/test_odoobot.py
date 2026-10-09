import base64
import io
from unittest.mock import patch

from PIL import Image

from odoo.tests import HttpCase, tagged

from odoo.addons.base.models.res_partner import ResPartner
from odoo.addons.twp_debrand.models.twp_debrand import PREFIX
from odoo.addons.twp_debrand_mail.hooks import _uninstall_hook


def png(color, size=(64, 64)):
    buffer = io.BytesIO()
    Image.new("RGB", size, color).save(buffer, "PNG")
    return base64.b64encode(buffer.getvalue())


@tagged("post_install", "-at_install", "twp_debrand")
class TestOdooBot(HttpCase):
    def setUp(self):
        super().setUp()
        self.bot = self.env.ref("base.partner_root")
        self.odoo_avatar = self.env["twp.debrand"]._odoo_bot_avatar()

    def save(self, **values):
        self.env["res.config.settings"].create(values).execute()

    def shown(self):
        return self.env["res.config.settings"].create({})

    def avatar_in_session(self):
        self.authenticate("admin", "admin")
        response = self.url_open("/odoo")
        self.assertEqual(response.status_code, 200)
        return '"twp_debrand_bot_avatar": true' in response.text

    def test_default_is_odoos(self):
        self.assertEqual(self.bot.name, "OdooBot")
        self.assertEqual(self.bot.image_1920, self.odoo_avatar)
        self.assertFalse(self.shown().twp_debrand_bot_name)
        self.assertFalse(self.shown().twp_debrand_bot_avatar)
        self.assertFalse(self.avatar_in_session())

    def test_rename_and_blank_restores(self):
        self.save(twp_debrand_bot_name="  Ada  ")
        self.assertEqual(self.bot.name, "Ada")
        self.assertEqual(self.shown().twp_debrand_bot_name, "Ada")
        self.save(twp_debrand_bot_name="")
        self.assertEqual(self.bot.name, "OdooBot")
        self.assertFalse(self.shown().twp_debrand_bot_name)

    def test_avatar_and_blank_restores(self):
        avatar = png("#1F5F8B")
        self.save(twp_debrand_bot_avatar=avatar)
        self.assertEqual(self.bot.image_1920, avatar)
        self.assertEqual(self.shown().twp_debrand_bot_avatar, avatar)
        self.assertTrue(self.avatar_in_session())
        self.save(twp_debrand_bot_avatar=False)
        self.assertEqual(self.bot.image_1920, self.odoo_avatar)
        self.assertFalse(self.avatar_in_session())

    def test_saving_settings_does_not_rewrite_odoobot(self):
        self.save(twp_debrand_bot_name="Ada", twp_debrand_bot_avatar=png("#16324F"))
        # The form sends back what get_values showed.
        shown = self.shown()
        with patch.object(ResPartner, "write", autospec=True, side_effect=ResPartner.write) as write:
            self.save(twp_debrand_bot_name=shown.twp_debrand_bot_name, twp_debrand_bot_avatar=shown.twp_debrand_bot_avatar)
        self.assertFalse([call for call in write.call_args_list if self.bot in call.args[0]])

    def test_uninstall_restores_odoobot_and_removes_params(self):
        self.save(twp_debrand_bot_name="Ada", twp_debrand_bot_avatar=png("#16324F"))
        _uninstall_hook(self.env)
        self.assertEqual(self.bot.name, "OdooBot")
        self.assertEqual(self.bot.image_1920, self.odoo_avatar)
        params = self.env["ir.config_parameter"].sudo()
        for key in ("email", "phone_home", "bot_avatar"):
            self.assertFalse(params.get_param(PREFIX + key), key)

    def test_public_discuss_page_title(self):
        channel = self.env["discuss.channel"].create({"name": "Harvest", "channel_type": "channel"})
        self.authenticate("admin", "admin")
        params = self.env["ir.config_parameter"].sudo()
        params.set_param("web.web_app_name", False)
        page = self.url_open(f"/discuss/channel/{channel.id}").text
        self.assertIn("<title>Odoo</title>", page)
        self.assertIn('href="/web/static/img/favicon.ico"', page)
        params.set_param("web.web_app_name", "Northfield")
        self.assertIn("<title>Northfield</title>", self.url_open(f"/discuss/channel/{channel.id}").text)
