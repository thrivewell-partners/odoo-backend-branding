from odoo import api, fields, models

from odoo.addons.twp_debrand.models.twp_debrand import PREFIX


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    twp_debrand_email = fields.Boolean(
        'Strip "Powered by Odoo" from emails', config_parameter=PREFIX + "email"
    )
    twp_debrand_phone_home = fields.Boolean(
        "Turn off the update check with odoo.com", config_parameter=PREFIX + "phone_home"
    )

    # Kept on OdooBot's partner, not as parameters: see twp.debrand._set_bot.
    twp_debrand_bot_name = fields.Char("OdooBot's name")
    twp_debrand_bot_avatar = fields.Image("OdooBot's avatar", attachment=False, max_width=1920, max_height=1920)

    @api.model
    def get_values(self):
        res = super().get_values()
        name, avatar = self.env["twp.debrand"]._bot_custom()
        res.update(twp_debrand_bot_name=name, twp_debrand_bot_avatar=avatar)
        return res

    def set_values(self):
        super().set_values()
        self.env["twp.debrand"]._set_bot((self.twp_debrand_bot_name or "").strip(), self.twp_debrand_bot_avatar)
