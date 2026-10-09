from odoo import models


class IrHttp(models.AbstractModel):
    _inherit = "ir.http"

    def session_info(self):
        info = super().session_info()
        info["twp_debrand_bot_avatar"] = self.env["twp.debrand"]._on("bot_avatar")
        return info
