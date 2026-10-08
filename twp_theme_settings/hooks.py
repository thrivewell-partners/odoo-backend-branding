from .models.twp_theme import PREFIX

# Odoo deletes a boolean setting when it is unticked, so "on unless the admin
# turns it off" has to be written once at install rather than read as a default.
DEFAULTS_ON = ("dark_enabled", "staging_marker")


def _post_init_hook(env):
    ICP = env["ir.config_parameter"].sudo()
    for key in DEFAULTS_ON:
        ICP.set_param(PREFIX + key, "True")
    env["twp.theme"]._regenerate()


def _uninstall_hook(env):
    # The generated SCSS attachments and the ir.asset records are module data
    # and go with the module. Downloaded font files are created at runtime, so
    # they are removed here, along with the module's settings.
    env["twp.theme"]._unlink_font_attachments()
    env["ir.config_parameter"].sudo().search([("key", "=like", PREFIX + "%")]).unlink()
    env["ir.attachment"].regenerate_assets_bundles()
