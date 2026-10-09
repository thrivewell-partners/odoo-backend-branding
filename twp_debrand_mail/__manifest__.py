{
    "name": "Branding: Discuss",
    "summary": "Takes Odoo's name out of emails, OdooBot and the Discuss screens. Installs itself when Discuss is present",
    "version": "19.0.0.1.0",
    "category": "Hidden",
    "license": "LGPL-3",
    "author": "ThriveWell Partners",
    "depends": ["twp_debrand", "mail"],
    "data": [
        "views/res_config_settings_views.xml",
        "views/mail_templates.xml",
        "views/discuss_public_templates.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "twp_debrand_mail/static/src/*.js",
        ],
    },
    "post_init_hook": "_post_init_hook",
    "uninstall_hook": "_uninstall_hook",
    "auto_install": True,
    "installable": True,
}
