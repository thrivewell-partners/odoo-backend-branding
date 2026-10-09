from odoo import api, models

# The one marker Odoo puts on a setting that only opens its Enterprise upgrade
# offer. Keying on it, not on a list of fields, covers apps installed later.
UPGRADE_WIDGET = "upgrade_boolean"
STATIC_HIDDEN = ("1", "True")


def _hidden(node):
    return node.get("invisible") in STATIC_HIDDEN


def _hide(node):
    node.set("invisible", "1")


def _elements(node):
    return [child for child in node if isinstance(child.tag, str)]


def _is_main_field(field, setting):
    # The web client treats a setting's first child, when it is a field, as the
    # setting itself: its label, its help and its Enterprise badge.
    children = _elements(setting)
    return bool(children) and children[0] is field


def _is_upgrade(field):
    return field.get("widget") == UPGRADE_WIDGET


def _visible_within(node, top):
    while node is not None and node is not top:
        if _hidden(node):
            return False
        node = node.getparent()
    return True


def _shows_something(block):
    return any(
        _visible_within(node, block) for node in block.iter("setting", "field", "widget", "button")
    )


def _hide_option(field, setting):
    """Hide an upgrade option nested in a setting that stays."""
    parent = field.getparent()
    if parent is not setting and all(_is_upgrade(f) for f in parent.iter("field")):
        # Its own row, as in "Quality worksheets" under quality control.
        _hide(parent)
        return
    _hide(field)
    for label in setting.iter("label"):
        if label.get("for") == field.get("name"):
            _hide(label)


def hide_upsells(arch):
    """Hide the settings that only open an Enterprise upgrade offer.

    A block left with nothing to show goes too, so its title and its help line
    do not stand over an empty box. Hidden nodes are never rendered, so the
    Settings search cannot find them either.
    """
    blocks = []
    for field in list(arch.iter("field")):
        if not _is_upgrade(field):
            continue
        setting = next(field.iterancestors("setting"), None)
        if setting is None:
            _hide(field)
        elif _is_main_field(field, setting):
            _hide(setting)
        else:
            _hide_option(field, setting)
        block = next(field.iterancestors("block"), None)
        if block is not None and block not in blocks:
            blocks.append(block)
    for block in blocks:
        if not _shows_something(block):
            _hide(block)
    return arch


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    # The combined view is cached, so the switch is part of the key: flipping it
    # picks the other cached arch with no upgrade and no cache to clear.

    @api.model
    def _get_view_cache_key(self, view_id=None, view_type="form", **options):
        key = super()._get_view_cache_key(view_id, view_type, **options)
        return key + (("twp_debrand_settings", self.env["twp.debrand"]._on("settings")),)

    @api.model
    def _get_view(self, view_id=None, view_type="form", **options):
        arch, view = super()._get_view(view_id, view_type, **options)
        if view_type == "form" and self.env["twp.debrand"]._on("settings"):
            hide_upsells(arch)
        return arch, view
