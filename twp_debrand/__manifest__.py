{
    "name": "Branding",
    "summary": "Removes Odoo's name, icons and upsells from the backend, login page, portal and emails",
    "version": "19.0.0.1.0",
    "category": "Extra Tools",
    "license": "LGPL-3",
    "author": "ThriveWell Partners",
    "depends": ["web", "base_setup"],
    "data": [
        "views/res_config_settings_views.xml",
        "views/webclient_templates.xml",
        "views/login_templates.xml",
        "views/settings_templates.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "twp_debrand/static/src/js/*.js",
        ],
    },
    "post_init_hook": "_post_init_hook",
    "uninstall_hook": "_uninstall_hook",
    "installable": True,
}
