from unittest.mock import patch

from odoo.tests import TransactionCase, tagged

from odoo.addons.mail.models import update
from odoo.addons.twp_debrand.models.twp_debrand import PREFIX
from odoo.addons.twp_debrand_mail.hooks import DEFAULTS_ON, _post_init_hook


@tagged("post_install", "-at_install", "twp_debrand")
class TestPhoneHome(TransactionCase):
    def check(self, on):
        self.env["ir.config_parameter"].sudo().set_param(PREFIX + "phone_home", "True" if on else False)
        # Never the network: the request is mocked either way.
        with patch.object(update.requests, "post") as post:
            post.return_value.text = "{'messages': []}"
            result = self.env["publisher_warranty.contract"].update_notification(cron_mode=False)
        return result, post

    def test_on_sends_nothing(self):
        result, post = self.check(True)
        self.assertTrue(result)
        post.assert_not_called()

    def test_off_is_odoos_check(self):
        result, post = self.check(False)
        self.assertTrue(result)
        post.assert_called_once()
        self.assertIn("arg0", post.call_args.kwargs["data"])

    def test_install_turns_it_on(self):
        params = self.env["ir.config_parameter"].sudo()
        for key in DEFAULTS_ON:
            params.set_param(PREFIX + key, False)
        _post_init_hook(self.env)
        for key in DEFAULTS_ON:
            self.assertTrue(self.env["twp.debrand"]._on(key), key)
