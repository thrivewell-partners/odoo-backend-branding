from odoo import fields, models


class ResUsersSettings(models.Model):
    _inherit = "res.users.settings"

    # Empty means the user has not chosen; the admin's default applies.
    twp_color_scheme = fields.Selection(
        [("light", "Light"), ("dark", "Dark")], string="Colour scheme"
    )
