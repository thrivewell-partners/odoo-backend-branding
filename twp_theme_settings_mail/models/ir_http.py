from odoo import models

CHATTER_POSITIONS = ("auto", "bottom", "side")


class IrHttp(models.AbstractModel):
    _inherit = "ir.http"

    def session_info(self):
        info = super().session_info()
        position = self.env["twp.theme"]._param("chatter_position", "auto")
        info["twp_chatter_position"] = position if position in CHATTER_POSITIONS else "auto"
        return info
