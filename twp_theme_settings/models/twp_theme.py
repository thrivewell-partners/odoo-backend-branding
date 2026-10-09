import base64
import logging
import re
from urllib.parse import quote_plus, urlparse

import requests
from markupsafe import Markup

from odoo import _, api, models
from odoo.exceptions import UserError

from .colors import contrast, ink, is_hex, mix

_logger = logging.getLogger(__name__)

PREFIX = "twp_theme_settings."
LIGHT_URL = "twp_theme_settings/static/twp_theme.scss"
DARK_URL = "twp_theme_settings/static/twp_theme_dark.scss"
FONT_TAG = "twp-font"

PALETTE = ("primary", "navbar", "success", "info", "warning", "danger", "bg", "view", "text")

# Odoo 19 Community's own values, used to derive dark colours when the admin
# has left a light colour blank.
ODOO_LIGHT = {
    "primary": "#71639E",
    "navbar": "#71639E",
    "success": "#28A745",
    "info": "#17A2B8",
    "warning": "#FFAC00",
    "danger": "#DC3545",
    "bg": "#F8F9FA",
    "view": "#FFFFFF",
    "text": "#212529",
}
DARK_NEUTRALS = {"bg": "#17191F", "view": "#20232B", "text": "#E5E7EB"}
DARK_NAVBAR_BASE = "#0B0D12"

SYSTEM_FONTS = (
    '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Ubuntu, '
    '"Noto Sans", Arial, sans-serif, "Apple Color Emoji", "Segoe UI Emoji", '
    '"Segoe UI Symbol", "Noto Color Emoji"'
)
FONT_NAME_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9 ]{0,59}$")
# Google serves woff2 only to browsers it recognises, as Odoo's website
# builder notes in website/models/assets.py.
WOFF2_HEADERS = {
    "user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0 Safari/537.36",
}
FONT_WEIGHTS = "400,400i,500,700,700i"


def derive_dark(light):
    return {
        "primary": mix(light["primary"], "#FFFFFF", 0.32),
        "navbar": mix(light["navbar"], DARK_NAVBAR_BASE, 0.45),
        "success": mix(light["success"], "#FFFFFF", 0.3),
        "info": mix(light["info"], "#FFFFFF", 0.3),
        "warning": mix(light["warning"], "#FFFFFF", 0.25),
        "danger": mix(light["danger"], "#FFFFFF", 0.3),
        **DARK_NEUTRALS,
    }


class TwpTheme(models.AbstractModel):
    _name = "twp.theme"
    _description = "Backend theme generator"

    # ------------------------------------------------------------------
    # Reading the admin's settings
    # ------------------------------------------------------------------

    @api.model
    def _param(self, key, default=False):
        return self.env["ir.config_parameter"].sudo().get_param(PREFIX + key, default)

    @api.model
    def _light_values(self):
        """The colours the admin set, blank ones left out."""
        values = {}
        for key in PALETTE:
            value = self._param(key)
            if is_hex(value):
                values[key] = value.upper()
        return values

    @api.model
    def _light_palette(self):
        return {**ODOO_LIGHT, **self._light_values()}

    @api.model
    def _dark_palette(self):
        derived = derive_dark(self._light_palette())
        palette = {}
        for key in PALETTE:
            value = self._param("dark_" + key)
            palette[key] = value.upper() if is_hex(value) else derived[key]
        return palette

    @api.model
    def _dark_enabled(self):
        return self._param("dark_enabled") == "True"

    # ------------------------------------------------------------------
    # SCSS generation
    # ------------------------------------------------------------------

    @api.model
    def _navbar_lines(self, navbar):
        text = ink(navbar)
        r, g, b = (int(text[i : i + 2], 16) for i in (1, 3, 5))
        return [
            f"$o-navbar-background: {navbar} !default;",
            f"$o-navbar-border-bottom: 1px solid {mix(navbar, '#000000', 0.18)} !default;",
            f"$o-navbar-entry-color: rgba({r}, {g}, {b}, 0.9) !default;",
            f"$o-navbar-entry-color--hover: {text} !default;",
            f"$o-navbar-brand-color: {text} !default;",
        ]

    @api.model
    def _palette_lines(self, palette):
        """Plain values only: these files load before Odoo's SCSS functions."""
        lines = []
        if "primary" in palette:
            lines.append(f"$o-brand-primary: {palette['primary']} !default;")
            # Odoo uses its Enterprise teal directly for selection outlines in
            # the colour picker, badges, signatures and the messaging menu.
            lines.append(f"$o-enterprise-action-color: {palette['primary']} !default;")
        if "navbar" in palette:
            # $o-brand-odoo also colours the loading bar, the export dialog
            # and the mobile search header.
            lines.append(f"$o-brand-odoo: {palette['navbar']} !default;")
            lines += self._navbar_lines(palette["navbar"])
        for key in ("success", "info", "warning", "danger"):
            if key in palette:
                lines.append(f"$o-{key}: {palette[key]} !default;")
        if "bg" in palette:
            lines.append(f"$o-webclient-background-color: {palette['bg']} !default;")
        if "view" in palette:
            lines.append(f"$o-view-background-color: {palette['view']} !default;")
        if "text" in palette:
            lines.append(f"$o-main-text-color: {palette['text']} !default;")
        return lines

    @api.model
    def _font_lines(self):
        lines = []
        body = self._param("font_body")
        head = self._param("font_head")
        if body:
            lines.append(f'$o-system-fonts: ("{body}", {SYSTEM_FONTS}) !default;')
        if head or body:
            lines.append(f'$o-headings-font-family: ("{head or body}", {SYSTEM_FONTS}) !default;')
        size = self._param("font_size")
        if size and size.isdigit() and 12 <= int(size) <= 18:
            px = int(size)
            lines.append(f"$o-font-size-base: {px / 16:.4f}rem !default;")
            lines.append(f"$o-font-size-base-small: {(px - 1) / 16:.4f}rem !default;")
            lines.append(f"$o-font-size-base-smaller: {(px - 2) / 16:.4f}rem !default;")
        radius = self._param("radius")
        if radius and radius.isdigit() and int(radius) <= 16:
            px = int(radius)
            lines.append(f"$o-border-radius: {px / 16:.4f}rem !default;")
            lines.append(f"$o-border-radius-sm: {max(px - 1, 0) / 16:.4f}rem !default;")
            lines.append(f"$o-border-radius-lg: {(px + 2) / 16:.4f}rem !default;")
        return lines

    @api.model
    def _font_face_css(self):
        css = []
        for key in ("font_body", "font_head"):
            attachment_id = self._param(key + "_css_id")
            if attachment_id and attachment_id.isdigit():
                attachment = self.env["ir.attachment"].sudo().browse(int(attachment_id)).exists()
                if attachment:
                    css.append(attachment.raw.decode())
        return css

    @api.model
    def _build_light_scss(self):
        lines = [
            "// Generated by twp_theme_settings from Settings > Backend Theme.",
            "// Edits here are overwritten on the next save.",
        ]
        lines += self._palette_lines(self._light_values())
        lines += self._font_lines()
        lines += self._font_face_css()
        return "\n".join(lines) + "\n"

    @api.model
    def _build_dark_scss(self):
        """Every colour the light file can set must be set here too.

        The dark file loads first in the dark bundle, so whatever it leaves
        unset falls through to the light file's value.
        """
        palette = self._dark_palette()
        view, text = palette["view"], palette["text"]
        grays = {
            100: palette["bg"],
            200: view,
            300: mix(view, text, 0.12),
            400: mix(view, text, 0.25),
            500: mix(view, text, 0.4),
            600: mix(view, text, 0.55),
            700: mix(view, text, 0.7),
            800: mix(view, text, 0.84),
            900: text,
        }
        lines = [
            "// Generated by twp_theme_settings from Settings > Backend Theme (dark).",
            "// Edits here are overwritten on the next save.",
            "$o-webclient-color-scheme: dark !default;",
            f"$o-white: {view} !default;",
            "$o-black: #FFFFFF !default;",
        ]
        lines += [f"$o-gray-{step}: {value} !default;" for step, value in grays.items()]
        lines += self._palette_lines(palette)
        lines += [
            f"$o-main-headings-color: {text} !default;",
            f"$o-main-link-color: {palette['primary']} !default;",
            f"$o-shadow-color: {palette['bg']} !default;",
            f"$o-form-lightsecondary: {grays[500]} !default;",
            f"$o-list-group-active-bg: {grays[300]} !default;",
        ]
        return "\n".join(lines) + "\n"

    @api.model
    def _write_generated(self, url, content):
        attachment = self.env["ir.attachment"].sudo().search(
            [("url", "=", url), ("type", "=", "binary")], limit=1
        )
        raw = content.encode()
        if attachment and attachment.raw != raw:
            attachment.write({"raw": raw})
        return attachment

    @api.model
    def _regenerate(self):
        """Rewrite both generated files and invalidate the backend bundles.

        Only the bundles that list these files recompile: the frontend, login,
        portal, report and POS bundles never include them.
        """
        self._write_generated(LIGHT_URL, self._build_light_scss())
        self._write_generated(DARK_URL, self._build_dark_scss())
        self.env.registry.clear_cache("assets")

    @api.model
    def _initial_b64(self, which):
        """Used by the data file, before any settings exist."""
        content = self._build_dark_scss() if which == "dark" else self._build_light_scss()
        return base64.b64encode(content.encode())

    # ------------------------------------------------------------------
    # Google Fonts, downloaded once and served from the database
    # ------------------------------------------------------------------

    @api.model
    def _validate_font_name(self, name):
        if not FONT_NAME_RE.match(name):
            raise UserError(
                _("'%s' is not a font name. Use the family name as Google Fonts shows it.", name)
            )

    @api.model
    def _fetch_google_font(self, name):
        """Download a Google Font family and store it as attachments.

        Returns the attachment holding the rewritten @font-face CSS. The font
        files are linked to it through original_id, so one unlink removes the
        set. This follows Odoo 19's website builder (website/models/assets.py).
        """
        self._validate_font_name(name)
        url = f"https://fonts.googleapis.com/css?family={quote_plus(name)}:{FONT_WEIGHTS}&display=swap"
        try:
            response = requests.get(url, timeout=10, headers=WOFF2_HEADERS)
        except requests.RequestException as e:
            raise UserError(
                _("Could not reach Google Fonts to download '%(name)s': %(error)s", name=name, error=e)
            ) from e
        if response.status_code != 200 or "@font-face" not in response.text:
            raise UserError(_("'%s' was not found on Google Fonts. Check the spelling.", name))

        Attachment = self.env["ir.attachment"].sudo()
        files = Attachment

        def store(match):
            nonlocal files
            src, font_format = match.group(1), match.group(2)
            if urlparse(src).hostname != "fonts.gstatic.com":
                raise UserError(_("Google Fonts returned an unexpected file location."))
            font = requests.get(src, timeout=10, headers=WOFF2_HEADERS)
            font.raise_for_status()
            filename = urlparse(src).path.lstrip("/").replace("/", "-")
            attachment = Attachment.create({
                "name": f"{FONT_TAG}-{filename}",
                "type": "binary",
                "raw": font.content,
                "public": True,
            })
            files |= attachment
            return f"src: url(/web/content/{attachment.id}/{filename}) {font_format}"

        try:
            css = re.sub(r"src: url\(([^)]+)\) ([^;]+)", store, response.text)
        except (requests.RequestException, UserError) as e:
            files.unlink()
            if isinstance(e, UserError):
                raise
            raise UserError(
                _("Downloading '%(name)s' failed part way: %(error)s", name=name, error=e)
            ) from e

        css_attachment = Attachment.create({
            "name": f"{name} ({FONT_TAG})",
            "type": "binary",
            "raw": css.encode(),
            "mimetype": "text/css",
            "public": True,
        })
        files.write({"original_id": css_attachment.id})
        return css_attachment

    @api.model
    def _unlink_font(self, attachment_id):
        if not attachment_id or not str(attachment_id).isdigit():
            return
        Attachment = self.env["ir.attachment"].sudo()
        Attachment.search([
            "|", ("id", "=", int(attachment_id)), ("original_id", "=", int(attachment_id)),
            ("name", "like", FONT_TAG),
        ]).unlink()

    @api.model
    def _unlink_font_attachments(self):
        self.env["ir.attachment"].sudo().search([("name", "like", FONT_TAG)]).unlink()

    @api.model
    def _set_font(self, key, name):
        """Store a font choice, downloading the files only when it changed."""
        ICP = self.env["ir.config_parameter"].sudo()
        name = " ".join((name or "").split())
        if name == (self._param(key) or ""):
            return
        old_css_id = self._param(key + "_css_id")
        if name:
            other = "font_head" if key == "font_body" else "font_body"
            if name == self._param(other) and self._param(other + "_css_id"):
                # Same family already downloaded for the other slot.
                css_id = self._param(other + "_css_id")
                ICP.set_param(PREFIX + key + "_css_id", css_id)
            else:
                css_id = self._fetch_google_font(name).id
                ICP.set_param(PREFIX + key + "_css_id", str(css_id))
        else:
            ICP.set_param(PREFIX + key + "_css_id", False)
        ICP.set_param(PREFIX + key, name or False)
        still_used = {self._param("font_body_css_id"), self._param("font_head_css_id")}
        if old_css_id and old_css_id not in still_used:
            self._unlink_font(old_css_id)

    # ------------------------------------------------------------------
    # Runtime layer: per company and per environment, no recompile
    # ------------------------------------------------------------------

    @api.model
    def _company_colors(self, company, dark):
        """A blank company colour falls back to the compiled theme."""
        if not dark:
            return {
                "navbar": company.twp_navbar_color if is_hex(company.twp_navbar_color) else None,
                "accent": company.twp_accent_color if is_hex(company.twp_accent_color) else None,
            }
        navbar = company.twp_navbar_color_dark
        if not is_hex(navbar):
            navbar = (
                mix(company.twp_navbar_color, DARK_NAVBAR_BASE, 0.45)
                if is_hex(company.twp_navbar_color)
                else None
            )
        accent = company.twp_accent_color_dark
        if not is_hex(accent):
            accent = (
                mix(company.twp_accent_color, "#FFFFFF", 0.32)
                if is_hex(company.twp_accent_color)
                else None
            )
        return {"navbar": navbar, "accent": accent}

    @api.model
    def _runtime_css(self, company, scheme):
        """CSS for one page load. Every value is a validated hex colour."""
        colors = self._company_colors(company, scheme == "dark")
        navbar, accent = colors["navbar"], colors["accent"]
        rules = []
        staging = (
            self.env["ir.config_parameter"].sudo().get_param("database.is_neutralized")
            and self._param("staging_marker") == "True"
        )
        if staging:
            stg = self._param("staging_color")
            navbar = stg.upper() if is_hex(stg) else "#B7472A"
        if navbar:
            text = ink(navbar)
            # The menu entries carry their own background, so the variables
            # Odoo reads for them are set along with the bar itself.
            hover = mix(navbar, "#FFFFFF" if scheme == "dark" else "#000000", 0.1)
            rules.append(
                f".o_main_navbar{{background:{navbar}!important;"
                f"border-bottom-color:{mix(navbar, '#000000', 0.18)}!important;"
                f"--NavBar-entry-color:{text};--NavBar-entry-color--hover:{text};"
                f"--NavBar-entry-color--active:{text};--NavBar-brand-color:{text};"
                f"--NavBar-entry-backgroundColor:{navbar};"
                f"--NavBar-entry-backgroundColor--hover:{hover};"
                f"--NavBar-entry-backgroundColor--focus:{hover};"
                f"--NavBar-entry-backgroundColor--active:{hover};}}"
                f".o_main_navbar .o_menu_brand{{color:{text}!important;}}"
                f".o_web_client{{--mobileSearch__header-bg:{navbar};}}"
                f".o_loading_indicator{{background-color:{navbar}!important;}}"
            )
        if staging:
            rules.append(
                ".o_main_navbar .o_menu_systray::before{content:'STAGING';"
                f"align-self:center;margin-inline:8px;padding:3px 7px;border-radius:3px;"
                f"font:700 11px/1 monospace;letter-spacing:.08em;"
                f"background:{ink(navbar)};color:{navbar};}}"
            )
        if accent:
            text = ink(accent)
            hover = mix(accent, "#000000" if scheme != "dark" else "#FFFFFF", 0.12)
            rules.append(
                f".o_web_client .btn-primary{{--btn-bg:{accent};--btn-border-color:{accent};"
                f"--btn-color:{text};--btn-hover-bg:{hover};--btn-hover-border-color:{hover};"
                f"--btn-hover-color:{text};--btn-active-bg:{hover};"
                f"--btn-active-border-color:{hover};--btn-active-color:{text};}}"
            )
        return Markup("".join(rules))

    # ------------------------------------------------------------------
    # Guardrail used by the Settings form
    # ------------------------------------------------------------------

    @api.model
    def _contrast_warnings(self):
        warnings = []
        for label, palette in (("Light", self._light_palette()), ("Dark", self._dark_palette())):
            pairs = [
                ("text on sheets", palette["text"], palette["view"]),
                ("text on page background", palette["text"], palette["bg"]),
                ("button text on primary", ink(palette["primary"]), palette["primary"]),
                ("navbar text on navbar", ink(palette["navbar"]), palette["navbar"]),
            ]
            for name, fg, bg in pairs:
                ratio = contrast(fg, bg)
                if ratio < 4.5:
                    warnings.append(f"{label}: {name} is {ratio:.1f}:1, below 4.5:1")
        return warnings
