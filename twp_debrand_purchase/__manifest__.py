{
    "name": "Branding: Purchase",
    "summary": "Removes Odoo's \"Connect with your software!\" offer from online purchase orders. Installs itself when Purchase is present",
    "version": "19.0.0.1.0",
    "category": "Hidden",
    "license": "LGPL-3",
    "author": "ThriveWell Partners",
    "depends": ["twp_debrand_portal", "purchase"],
    "data": [
        "views/purchase_portal_templates.xml",
    ],
    "auto_install": True,
    "installable": True,
}
