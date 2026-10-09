{
    "name": "Branding: Portal",
    "summary": "Removes \"Powered by Odoo\" from portal documents. Installs itself when the portal is present",
    "version": "19.0.0.1.0",
    "category": "Hidden",
    "license": "LGPL-3",
    "author": "ThriveWell Partners",
    "depends": ["twp_debrand", "portal"],
    "data": [
        "views/portal_templates.xml",
    ],
    "auto_install": True,
    "installable": True,
}
