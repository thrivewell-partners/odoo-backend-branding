from odoo.tests import TransactionCase, tagged

from odoo.addons.twp_debrand.models.twp_debrand import PREFIX


@tagged("post_install", "-at_install", "twp_debrand")
class TestPaymentProviders(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.admin = cls.env.ref("base.user_admin")
        # As the admin throughout: providers carry a company rule.
        cls.Provider = cls.env["payment.provider"].with_user(cls.admin)
        # SEPA Direct Debit is the one payment ships; any provider will do.
        cls.enterprise = cls.Provider.search([("module_to_buy", "=", True)], limit=1)
        if not cls.enterprise:
            cls.enterprise = cls.Provider.search([], limit=1)
            cls.enterprise.module_id = cls.env["ir.module.module"].search([("to_buy", "=", True)], limit=1)

    def switch(self, on):
        self.env["ir.config_parameter"].sudo().set_param(PREFIX + "settings", "True" if on else False)

    def listed(self):
        result = self.Provider.web_search_read([], {"name": {}})
        return {record["id"] for record in result["records"]}

    def grouped_count(self):
        groups = self.Provider.web_read_group([], ["state"])["groups"]
        return sum(group["__count"] for group in groups)

    def test_enterprise_provider_hidden_when_on(self):
        self.switch(True)
        listed = self.listed()
        self.assertNotIn(self.enterprise.id, listed)
        self.assertEqual(listed, set(self.Provider.search([("module_to_buy", "=", False)]).ids))
        self.assertEqual(self.grouped_count(), len(listed))

    def test_off_is_odoos_list(self):
        self.switch(False)
        self.assertIn(self.enterprise.id, self.listed())
        self.assertEqual(self.grouped_count(), self.Provider.search_count([]))

    def test_orm_still_finds_it(self):
        # Payment flows search providers through the ORM; only the list is narrowed.
        self.switch(True)
        self.assertIn(self.enterprise, self.Provider.search([]))
