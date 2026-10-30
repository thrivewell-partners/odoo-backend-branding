{
    "name": "Report Fonts",
    "summary": "Brand fonts for PDF documents, with a separate heading font, chosen in the Document Layout",
    "version": "19.0.0.1.0",
    "category": "Extra Tools",
    "license": "LGPL-3",
    "author": "ThriveWell Partners",
    "depends": ["web"],
    "data": [
        "views/report_templates.xml",
        "views/base_document_layout_views.xml",
    ],
    "assets": {
        # The font files ship with the module, so wkhtmltopdf loads them from
        # this server like Odoo's own report fonts, never from Google.
        "web.report_assets_common": [
            (
                "after",
                "web/static/fonts/fonts.scss",
                "twp_report_fonts/static/src/scss/report_fonts.scss",
            ),
        ],
    },
    "uninstall_hook": "_uninstall_hook",
    "installable": True,
}
