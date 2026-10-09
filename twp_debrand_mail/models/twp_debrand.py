import base64

from odoo import api, models
from odoo.tools import file_open

from odoo.addons.twp_debrand.models.twp_debrand import PREFIX

# What mail/data/res_partner_data.xml gives the system partner.
ODOO_BOT_NAME = "OdooBot"
ODOO_BOT_AVATAR = "mail/static/src/img/odoobot.png"


class TwpDebrand(models.AbstractModel):
    _inherit = "twp.debrand"

    # OdooBot is base.partner_root, the author of automatic messages. Its name
    # and avatar live on that partner, so the partner is the only copy.

    @api.model
    def _bot(self):
        return self.env.ref("base.partner_root").sudo()

    @api.model
    def _odoo_bot_avatar(self):
        with file_open(ODOO_BOT_AVATAR, "rb") as image:
            return base64.b64encode(image.read())

    @api.model
    def _bot_custom(self):
        """OdooBot's name and avatar where they differ from Odoo's, else False."""
        bot = self._bot()
        name = bot.name if bot.name != ODOO_BOT_NAME else False
        avatar = bot.image_1920 if bot.image_1920 != self._odoo_bot_avatar() else False
        return name, avatar

    @api.model
    def _set_bot(self, name, avatar):
        """Rename OdooBot and change its avatar. Blank puts back Odoo's."""
        bot = self._bot()
        odoo_avatar = self._odoo_bot_avatar()
        if isinstance(avatar, str):
            avatar = avatar.encode()
        avatar = avatar or odoo_avatar
        values = {}
        if bot.name != (name or ODOO_BOT_NAME):
            values["name"] = name or ODOO_BOT_NAME
        if bot.image_1920 != avatar:
            values["image_1920"] = avatar
        if values:
            bot.write(values)
        # Read by session_info: the browser only swaps OdooBot's icon when there is a new one.
        self.env["ir.config_parameter"].sudo().set_param(
            PREFIX + "bot_avatar", "True" if avatar != odoo_avatar else False
        )
