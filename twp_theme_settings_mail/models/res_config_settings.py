from odoo import fields, models

from odoo.addons.twp_theme_settings.models.twp_theme import PREFIX


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    twp_chatter_position = fields.Selection(
        [("auto", "Odoo's default"), ("bottom", "Always below"), ("side", "Beside the form")],
        string="Chatter position",
        config_parameter=PREFIX + "chatter_position",
        default="auto",
    )
