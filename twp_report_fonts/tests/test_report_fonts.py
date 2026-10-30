import posixpath
import re

from odoo.tests import TransactionCase, tagged
from odoo.tools.misc import file_open

from odoo.addons.twp_report_fonts.hooks import _uninstall_hook
from odoo.addons.twp_report_fonts.models.res_company import FONTS

SCSS = "twp_report_fonts/static/src/scss/report_fonts.scss"


@tagged("post_install", "-at_install", "twp_report_fonts")
class TestReportFonts(TransactionCase):
    def setUp(self):
        super().setUp()
        # Start from Odoo's fonts whatever the database has saved.
        self.env["res.company"].search([]).write({"font": "Lato", "twp_heading_font": False})
        self.company = self.env.company

    def company_styles(self):
        return self.env.ref("web.asset_styles_company_report").raw.decode()

    def test_fonts_offered_for_text_and_headings(self):
        for field in ("font", "twp_heading_font"):
            values = dict(self.company._fields[field]._description_selection(self.env))
            self.assertEqual(values.get("Barlow"), "Barlow")
            self.assertEqual(values.get("Barlow_Semi_Condensed"), "Barlow Semi Condensed")
            self.assertIn("Lato", values, "Odoo's own fonts are still offered")

    def test_font_files_ship_with_the_module(self):
        scss = file_open(SCSS).read()
        for family in FONTS:
            self.assertIn(f"'{family}'", scss)
            with file_open(f"twp_report_fonts/static/fonts/{family}/OFL.txt") as licence:
                self.assertIn("SIL Open Font License", licence.read())
        for line in scss.splitlines():
            if line.startswith("@include twp-report-font("):
                family, file = (part.strip(" '") for part in line[25:].split(",")[:2])
                with file_open(f"twp_report_fonts/static/fonts/{family}/{file}.ttf", "rb") as ttf:
                    self.assertEqual(ttf.read(4), b"\x00\x01\x00\x00", f"{file} is a TrueType file")

    def test_report_bundle_loads_the_faces_after_odoos(self):
        files, _external = self.env["ir.qweb"]._get_asset_content("web.report_assets_common")
        urls = [f["url"] for f in files]
        self.assertIn("/" + SCSS, urls)
        self.assertEqual(urls.index("/" + SCSS), urls.index("/web/static/fonts/fonts.scss") + 1)

    def test_compiled_faces_point_at_the_files(self):
        # wkhtmltopdf fetches these over HTTP; a wrong path still renders, in
        # a fallback font, so the compiled bundle is checked here.
        bundle = self.env["ir.qweb"]._get_asset_bundle("web.report_assets_common", js=False)
        css = "".join(attachment.raw.decode() for attachment in bundle.css())
        urls = set(re.findall(r"url\(['\"]?([^'\")]*twp_report_fonts[^'\")]*)", css))
        self.assertEqual(len(urls), 8)
        for url in urls:
            path = posixpath.normpath(url)
            self.assertTrue(path.startswith("/twp_report_fonts/static/fonts/"), url)
            with file_open(path.lstrip("/"), "rb") as ttf:
                self.assertTrue(ttf.read(4))

    def test_text_and_heading_reach_the_company_styles(self):
        self.company.write({"font": "Barlow", "twp_heading_font": "Barlow_Semi_Condensed"})
        styles = self.company_styles()
        self.assertIn("font-family: Barlow;", styles)
        self.assertIn("font-family: Barlow_Semi_Condensed, Barlow;", styles)

    def test_blank_heading_adds_nothing(self):
        self.company.write({"font": "Barlow", "twp_heading_font": "Barlow_Semi_Condensed"})
        self.company.twp_heading_font = False
        styles = self.company_styles()
        self.assertIn("font-family: Barlow;", styles)
        self.assertNotIn("Barlow_Semi_Condensed", styles)
        self.assertNotIn("h1, h2", styles)

    def test_heading_font_is_per_company(self):
        other = self.env["res.company"].create({"name": "Second Company"})
        self.company.twp_heading_font = "Barlow_Semi_Condensed"
        styles = self.company_styles()
        def has_heading_rule(company):
            return re.search(rf"\.o_company_{company.id}_layout \{{\s*h1", styles)

        self.assertTrue(has_heading_rule(self.company))
        self.assertFalse(has_heading_rule(other))

    def test_document_layout_preview(self):
        wizard = self.env["base.document.layout"].create({"company_id": self.company.id})
        wizard.report_layout_id = self.env["report.layout"].search([], limit=1)
        wizard.font = "Barlow"
        self.assertNotIn("Barlow_Semi_Condensed", wizard.preview)
        wizard.twp_heading_font = "Barlow_Semi_Condensed"
        self.assertIn("font-family: Barlow_Semi_Condensed, Barlow", wizard.preview)

    def test_uninstall_returns_to_odoos_fonts(self):
        self.company.write({"font": "Barlow_Semi_Condensed", "twp_heading_font": "Barlow"})
        _uninstall_hook(self.env)
        self.assertEqual(self.company.font, "Lato")
        self.assertFalse(self.company.twp_heading_font)
        self.assertNotIn("Barlow", self.company_styles())
