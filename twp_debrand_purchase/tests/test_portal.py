from odoo.tests import HttpCase, tagged

from odoo.addons.twp_debrand.models.twp_debrand import PREFIX


@tagged("post_install", "-at_install", "twp_debrand")
class TestConnectSoftware(HttpCase):
    # As in the Sales bridge: the button needs a structured format installed.
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        vendor = cls.env["res.partner"].create({"name": "TWP Portal Vendor"})
        product = cls.env["product.product"].create({"name": "TWP Portal Part", "standard_price": 10})
        cls.order = cls.env["purchase.order"].create({
            "partner_id": vendor.id,
            "order_line": [(0, 0, {"product_id": product.id, "product_qty": 1})],
        })
        cls.order._portal_ensure_token()

    def page(self, on):
        self.env["ir.config_parameter"].sudo().set_param(PREFIX + "connect_software", "True" if on else False)
        response = self.url_open(f"/my/purchase/{self.order.id}?access_token={self.order.access_token}")
        self.assertEqual(response.status_code, 200)
        return response.text

    def test_on(self):
        html = self.page(True)
        self.assertNotIn("Connect with your software", html)
        self.assertNotIn("portal_connect_software_modal", html)
        self.assertNotIn("Start on Odoo", html)
        self.assertIn(self.order.name, html, "the rest of the page still renders")

    def test_off(self):
        if not self.order._get_edi_builders():
            self.skipTest("no structured format installed, so Odoo shows no button either")
        html = self.page(False)
        self.assertIn("Connect with your software", html)
        self.assertIn("Start on Odoo", html)
