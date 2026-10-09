{
    "name": "Backend Theme: Discuss",
    "summary": "Chatter position for the Backend Theme. Installs itself when Discuss is present",
    "version": "19.0.0.1.1",
    "category": "Hidden",
    "license": "LGPL-3",
    "author": "ThriveWell Partners",
    "depends": ["twp_theme_settings", "mail"],
    "data": [
        "views/res_config_settings_views.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "twp_theme_settings_mail/static/src/chatter_position.js",
        ],
    },
    "auto_install": True,
    "installable": True,
}
