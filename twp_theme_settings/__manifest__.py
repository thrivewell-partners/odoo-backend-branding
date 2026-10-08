{
    "name": "Backend Theme",
    "summary": "Colours, fonts and dark mode for the backend, set by the admin in Settings",
    "version": "19.0.0.1.0",
    "category": "Extra Tools",
    "license": "LGPL-3",
    "author": "ThriveWell Partners",
    "depends": ["web", "base_setup"],
    "external_dependencies": {"python": ["requests"]},
    "data": [
        "data/twp_theme_assets.xml",
        "views/res_config_settings_views.xml",
        "views/res_company_views.xml",
        "views/webclient_templates.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "twp_theme_settings/static/src/js/color_scheme_service.js",
        ],
        # Structural dark-mode styling. The admin's dark palette is generated
        # into an attachment and prepended by data/twp_theme_assets.xml.
        "web.assets_web_dark": [
            (
                "after",
                "web/static/lib/bootstrap/scss/_functions.scss",
                "twp_theme_settings/static/src/scss/dark/bs_functions.dark.scss",
            ),
            (
                "before",
                "web/static/src/scss/bootstrap_overridden.scss",
                "twp_theme_settings/static/src/scss/dark/bootstrap.dark.scss",
            ),
        ],
        "web.assets_backend_lazy_dark": [
            (
                "after",
                "web/static/lib/bootstrap/scss/_functions.scss",
                "twp_theme_settings/static/src/scss/dark/bs_functions.dark.scss",
            ),
            (
                "before",
                "web/static/src/scss/bootstrap_overridden.scss",
                "twp_theme_settings/static/src/scss/dark/bootstrap.dark.scss",
            ),
        ],
    },
    "post_init_hook": "_post_init_hook",
    "uninstall_hook": "_uninstall_hook",
    "installable": True,
}
