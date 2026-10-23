{
    "name": "Branding: Sales",
    "summary": "Removes Odoo's \"Connect with your software!\" offer from online quotes and orders. Installs itself when Sales is present",
    "version": "19.0.0.1.0",
    "category": "Hidden",
    "license": "LGPL-3",
    "author": "ThriveWell Partners",
    "depends": ["twp_debrand_portal", "sale"],
    "data": [
        "views/sale_portal_templates.xml",
    ],
    "auto_install": True,
    "installable": True,
}
