{
    "name": "Branding: Portal",
    "summary": "Removes \"Powered by Odoo\" and Odoo's \"Connect with your software!\" offer from portal documents. Installs itself when the portal is present",
    "version": "19.0.0.2.0",
    "category": "Hidden",
    "license": "LGPL-3",
    "author": "ThriveWell Partners",
    "depends": ["twp_debrand", "portal"],
    "data": [
        "views/res_config_settings_views.xml",
        "views/portal_templates.xml",
    ],
    "post_init_hook": "_post_init_hook",
    "uninstall_hook": "_uninstall_hook",
    "auto_install": True,
    "installable": True,
}
