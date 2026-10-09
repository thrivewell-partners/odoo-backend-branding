from odoo.tests import TransactionCase, tagged

from odoo.addons.twp_debrand.models.twp_debrand import PREFIX


@tagged("post_install", "-at_install", "twp_debrand")
class TestPortalSidebar(TransactionCase):
    # The sidebar sits on every portal quote, order and invoice. Portal alone
    # has no such page, so the template is rendered directly.
    def sidebar(self):
        return str(self.env["ir.qweb"]._render(
            "portal.portal_record_sidebar", {"classes": "", "title": "S00042", "entries": ""}
        ))

    def test_promotion_switch(self):
        ICP = self.env["ir.config_parameter"].sudo()
        ICP.set_param(PREFIX + "promotion", False)
        html = self.sidebar()
        self.assertIn("Powered by", html)
        self.assertIn("utm_medium=portal", html)
        ICP.set_param(PREFIX + "promotion", "True")
        html = self.sidebar()
        self.assertNotIn("Powered by", html)
        self.assertNotIn("odoo.com", html)
        self.assertIn("S00042", html, "the rest of the sidebar still renders")
