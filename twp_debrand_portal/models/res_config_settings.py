from odoo import fields, models

from odoo.addons.twp_debrand.models.twp_debrand import PREFIX


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    # Read by the Sales and Purchase bridges, which own the pages it appears on.
    twp_debrand_connect_software = fields.Boolean(
        'Hide "Connect with your software!"', config_parameter=PREFIX + "connect_software"
    )
