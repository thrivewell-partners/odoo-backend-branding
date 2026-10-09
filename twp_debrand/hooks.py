from .models.twp_debrand import PREFIX

# Odoo deletes a boolean setting when it is unticked, so "on unless the admin
# turns it off" has to be written once at install rather than read as a default.
# Installing the module is asking for the branding to go. Bridges add their own.
DEFAULTS_ON = ("user_menu", "login_powered", "login_databases", "promotion", "settings")


def _post_init_hook(env):
    env["twp.debrand"]._switch_on(DEFAULTS_ON)


def _uninstall_hook(env):
    # The icon is created at runtime, so it is removed here with the settings.
    env["twp.debrand"]._unlink_icon()
    env["ir.config_parameter"].sudo().search([("key", "=like", PREFIX + "%")]).unlink()
