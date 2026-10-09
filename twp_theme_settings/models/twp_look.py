"""A look as a file: the theme settings of one database, loaded into another.

The file is JSON. Each setting is keyed by its Settings field name without the
"twp_" prefix, and a blank setting is null, so loading a file gives the same
look as the database it came from.
"""

import base64
import binascii
import json

from odoo import _, api, fields, models
from odoo.exceptions import UserError

from .colors import is_hex
from .res_config_settings import CHECKED_COLORS
from .twp_theme import FONT_NAME_RE, PALETTE

LOOK_FORMAT = "twp-backend-look"
LOOK_VERSION = 1
FIELD_PREFIX = "twp_"
MAX_FILE_BYTES = 25 * 1024 * 1024
MAX_TEXT = 200


class TwpTheme(models.AbstractModel):
    _inherit = "twp.theme"

    @api.model
    def _export_look(self):
        Settings = self.env["res.config.settings"]
        names = Settings._twp_look_fields()
        current = Settings.default_get(names)
        values = {}
        for name in names:
            value = current.get(name)
            if isinstance(value, bytes):
                value = value.decode()
            values[name.removeprefix(FIELD_PREFIX)] = value if value not in (False, "") else None
        return {
            "format": LOOK_FORMAT,
            "version": LOOK_VERSION,
            "exported": fields.Date.to_string(fields.Date.today()),
            "settings": values,
        }

    @api.model
    def _read_look(self, raw):
        """Settings values from a look file, checked. Returns (values, ignored keys)."""
        if len(raw) > MAX_FILE_BYTES:
            raise UserError(_("This file is too large to be a look file."))
        try:
            data = json.loads(raw)
        except (UnicodeDecodeError, ValueError) as e:
            raise UserError(_("This file is not a look file. Download one from Settings > Backend Theme.")) from e
        if not isinstance(data, dict) or data.get("format") != LOOK_FORMAT:
            raise UserError(_("This file is not a look file. Download one from Settings > Backend Theme."))
        if data.get("version") != LOOK_VERSION:
            raise UserError(_("This look file was made by a newer version of Backend Theme. Update the module first."))
        settings = data.get("settings")
        if not isinstance(settings, dict):
            raise UserError(_("This look file has no settings in it."))

        Settings = self.env["res.config.settings"]
        names = Settings._twp_look_fields()
        ignored = sorted(key for key in settings if FIELD_PREFIX + key not in names)
        values = {}
        for name in names:
            key = name.removeprefix(FIELD_PREFIX)
            values[name] = self._look_value(Settings._fields[name], key, settings.get(key))
        return values, ignored

    @api.model
    def _look_value(self, field, key, value):
        """One setting from a look file, checked against its Settings field."""
        if value is None or value == "":
            return False

        def refuse():
            raise UserError(self.env._("The look file has an unusable value for %(setting)s.", setting=key))

        if field.type == "boolean":
            if not isinstance(value, bool):
                refuse()
            return value
        if field.type == "selection":
            if value not in {option for option, _label in field.selection}:
                refuse()
            return value
        if field.type == "binary":
            if not isinstance(value, str):
                refuse()
            try:
                base64.b64decode(value, validate=True)
            except (binascii.Error, ValueError):
                refuse()
            return value
        if not isinstance(value, str):
            refuse()
        if field.name in CHECKED_COLORS:
            if not is_hex(value):
                refuse()
            return value.upper()
        if field.name in ("twp_font_body", "twp_font_head"):
            if not FONT_NAME_RE.match(value):
                refuse()
            return value
        return value[:MAX_TEXT]

    @api.model
    def _apply_look(self, values):
        """Save the values the way the Settings form does, so the same checks,
        font downloads and regeneration run."""
        self.env["res.config.settings"].create(values).set_values()

    @api.model
    def _look_summary(self, values, ignored):
        """What loading the file will change, in a few lines."""
        light = [f"{key} {values[FIELD_PREFIX + key]}" for key in PALETTE if values[FIELD_PREFIX + key]]
        dark = [key for key in PALETTE if values[f"{FIELD_PREFIX}dark_{key}"]]
        fonts = [font for font in (values["twp_font_body"], values["twp_font_head"]) if font]
        lines = [
            _("Colours: %(colours)s.", colours=", ".join(light)) if light else _("Colours: Odoo's own."),
        ]
        if dark:
            lines.append(_("Dark colours set by hand: %(keys)s.", keys=", ".join(dark)))
        lines.append(
            _("Fonts: %(fonts)s, downloaded from Google Fonts when you load the look.", fonts=", ".join(fonts))
            if fonts else _("Fonts: Odoo's own.")
        )
        settings_fields = self.env["res.config.settings"]._fields

        def label(name):
            value = values[name] or settings_fields[name].default(self)
            return dict(settings_fields[name]._description_selection(self.env)).get(value, value)

        lines.append(_(
            "Text %(size)s, corners %(radius)s, %(density)s rows, %(width)s forms.",
            size=label("twp_font_size"), radius=label("twp_radius"),
            density=label("twp_density").lower(), width=label("twp_sheet_width").lower(),
        ))
        lines.append(
            _("Dark mode switch: on.") if values["twp_dark_enabled"] else _("Dark mode switch: off.")
        )
        lines.append(
            _("Branded login page: on.") if values["twp_login_enabled"] else _("Branded login page: off.")
        )
        if ignored:
            lines.append(_("Not used in this database: %(keys)s.", keys=", ".join(ignored)))
        return "\n".join(lines)


class TwpThemeLookImport(models.TransientModel):
    _name = "twp.theme.look.import"
    _description = "Load a backend look from a file"

    look_file = fields.Binary("Look file", required=True)
    look_filename = fields.Char("File name")
    summary = fields.Text(compute="_compute_summary")
    look_error = fields.Boolean(compute="_compute_summary")

    @api.depends("look_file")
    def _compute_summary(self):
        for wizard in self:
            wizard.summary, wizard.look_error = False, False
            if not wizard.look_file:
                continue
            try:
                values, ignored = self.env["twp.theme"]._read_look(base64.b64decode(wizard.look_file))
                wizard.summary = self.env["twp.theme"]._look_summary(values, ignored)
            except UserError as e:
                wizard.summary, wizard.look_error = e.args[0], True

    def action_load(self):
        self.ensure_one()
        values, _ignored = self.env["twp.theme"]._read_look(base64.b64decode(self.look_file))
        self.env["twp.theme"]._apply_look(values)
        return {"type": "ir.actions.client", "tag": "reload"}
