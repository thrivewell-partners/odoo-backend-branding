import json

from werkzeug.exceptions import Forbidden

from odoo import fields, http
from odoo.http import content_disposition, request


class LookController(http.Controller):
    @http.route("/twp_theme_settings/look", type="http", auth="user", methods=["GET"])
    def download_look(self):
        """The saved look as a file, for Settings > Backend Theme on another database."""
        if not request.env.user.has_group("base.group_system"):
            raise Forbidden()
        look = request.env["twp.theme"]._export_look()
        filename = f"backend-look-{fields.Date.to_string(fields.Date.context_today(request.env.user))}.json"
        return request.make_response(
            json.dumps(look, indent=2),
            headers=[
                ("Content-Type", "application/json"),
                ("Content-Disposition", content_disposition(filename)),
            ],
        )
