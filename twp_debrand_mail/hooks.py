from odoo.addons.twp_debrand.models.twp_debrand import PREFIX

# Installing is asking for the branding to go, as in twp_debrand.
DEFAULTS_ON = ("email", "phone_home")
KEYS = DEFAULTS_ON + ("bot_avatar",)


def _post_init_hook(env):
    env["twp.debrand"]._switch_on(DEFAULTS_ON)


def _uninstall_hook(env):
    # OdooBot's name and avatar were written on its partner, so they go back to Odoo's.
    env["twp.debrand"]._set_bot(False, False)
    env["ir.config_parameter"].sudo().search([("key", "in", [PREFIX + key for key in KEYS])]).unlink()
