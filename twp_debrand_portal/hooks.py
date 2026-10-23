from odoo.addons.twp_debrand.models.twp_debrand import PREFIX

# Installing is asking for the branding to go, as in twp_debrand.
DEFAULTS_ON = ("connect_software",)


def _post_init_hook(env):
    env["twp.debrand"]._switch_on(DEFAULTS_ON)


def _uninstall_hook(env):
    env["ir.config_parameter"].sudo().search([("key", "in", [PREFIX + key for key in DEFAULTS_ON])]).unlink()
