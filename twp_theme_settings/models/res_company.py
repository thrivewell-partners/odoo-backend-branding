from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

from .colors import is_hex

COMPANY_COLOR_FIELDS = (
    "twp_navbar_color",
    "twp_navbar_color_dark",
    "twp_accent_color",
    "twp_accent_color_dark",
)


class ResCompany(models.Model):
    _inherit = "res.company"

    twp_navbar_color = fields.Char("Navbar colour", help="Blank uses the theme's navbar colour.")
    twp_navbar_color_dark = fields.Char(
        "Navbar colour, dark", help="Blank works it out from the light navbar colour."
    )
    twp_accent_color = fields.Char("Accent colour", help="Primary buttons. Blank uses the theme.")
    twp_accent_color_dark = fields.Char(
        "Accent colour, dark", help="Blank works it out from the light accent colour."
    )

    twp_navbar_logo = fields.Image(
        "Navbar logo",
        max_width=600,
        max_height=150,
        help="Shown in the navbar beside the apps menu while this company is selected. "
        "A wide logo with a transparent background works best.",
    )

    @api.constrains(*COMPANY_COLOR_FIELDS)
    def _check_twp_colors(self):
        for company in self:
            for name in COMPANY_COLOR_FIELDS:
                value = company[name]
                if value and not is_hex(value):
                    raise ValidationError(
                        _("%(field)s must be a colour like #1F5F8B.", field=self._fields[name].string)
                    )
