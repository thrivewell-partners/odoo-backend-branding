from lxml import etree

from odoo.tests import TransactionCase, tagged

from odoo.addons.twp_debrand.models.settings_upsells import hide_upsells
from odoo.addons.twp_debrand.models.twp_debrand import PREFIX


def hidden(node):
    """Whether the web client would skip the node: it or a parent is invisible="1"."""
    return any(n.get("invisible") in ("1", "True") for n in (node, *node.iterancestors()))


@tagged("post_install", "-at_install", "twp_debrand")
class TestSettings(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.admin = cls.env.ref("base.user_admin")
        # General Settings shows its one upsell (inter-company rules) to
        # multi-company users only, and it must be in the arch to be checked.
        cls.admin.group_ids += cls.env.ref("base.group_multi_company")
        cls.Module = cls.env["ir.module.module"]
        cls.to_buy = cls.Module.search([("to_buy", "=", True)])

    def switch(self, on):
        self.env["ir.config_parameter"].sudo().set_param(PREFIX + "settings", "True" if on else False)

    def settings_arch(self):
        views = self.env["res.config.settings"].with_user(self.admin).get_views([(False, "form")])
        return etree.fromstring(views["views"]["form"]["arch"])

    def upgrade_fields(self, arch):
        fields = arch.xpath("//field[@widget='upgrade_boolean']")
        self.assertTrue(fields, "base_setup has an upgrade setting; the arch must carry it")
        return fields

    # Settings: upgrade offers.

    def test_upsells_hidden_when_on(self):
        self.switch(True)
        arch = self.settings_arch()
        for field in self.upgrade_fields(arch):
            self.assertTrue(hidden(field), f"{field.get('name')} is an upgrade offer and must be hidden")
        setting = arch.xpath("//setting[@id='inter_company']")[0]
        self.assertEqual(setting.get("invisible"), "1", "the whole row goes, label and help with it")

    def test_off_is_odoos_settings(self):
        self.switch(False)
        arch = self.settings_arch()
        for field in self.upgrade_fields(arch):
            self.assertFalse(hidden(field), f"{field.get('name')} must show as Odoo shows it")

    def test_switch_flips_without_upgrade(self):
        # The view is cached; each state must get its own arch, not the last one.
        self.switch(True)
        on = etree.tostring(self.settings_arch())
        self.switch(False)
        off = etree.tostring(self.settings_arch())
        self.assertNotEqual(on, off)
        self.switch(True)
        self.assertEqual(etree.tostring(self.settings_arch()), on)

    def test_rule_covers_any_module(self):
        # A module installed later is covered by the widget alone. Shapes from
        # account (Fiscal Periods), mrp and stock (quality worksheets).
        arch = etree.fromstring("""
            <form><app name="later">
                <block title="Fiscal Periods" help="A line under the title" name="only_upsells">
                    <setting id="placeholder" invisible="1"/>
                    <setting id="reports"><field name="module_reports" widget="upgrade_boolean"/></setting>
                </block>
                <block title="Mixed" name="mixed">
                    <setting id="free"><field name="free_a"/>
                        <div class="row" id="worksheet_row">
                            <field name="module_worksheet" widget="upgrade_boolean"/>
                            <div><label for="module_worksheet"/></div>
                        </div>
                    </setting>
                    <setting id="free_b"><field name="free_b"/>
                        <field name="module_side" widget="upgrade_boolean"/><label for="module_side"/>
                    </setting>
                    <setting id="quality"><field name="module_quality" widget="upgrade_boolean"/>
                        <div class="row" id="quality_row" invisible="not module_quality">
                            <field name="module_quality_worksheet" widget="upgrade_boolean"/>
                        </div>
                    </setting>
                </block>
            </app></form>
        """)
        hide_upsells(arch)

        def node(xpath):
            return arch.xpath(xpath)[0]

        self.assertEqual(node("//setting[@id='reports']").get("invisible"), "1")
        self.assertEqual(
            node("//block[@name='only_upsells']").get("invisible"), "1",
            "a block left empty goes, title and help with it",
        )
        self.assertFalse(hidden(node("//block[@name='mixed']")))
        self.assertFalse(hidden(node("//setting[@id='free']")), "a free setting with an upgrade option stays")
        self.assertEqual(node("//div[@id='worksheet_row']").get("invisible"), "1")
        self.assertFalse(hidden(node("//field[@name='free_b']")))
        self.assertEqual(node("//field[@name='module_side']").get("invisible"), "1")
        self.assertEqual(node("//label[@for='module_side']").get("invisible"), "1")
        self.assertEqual(node("//setting[@id='quality']").get("invisible"), "1")

    # Settings: the About box.

    def test_about_follows_the_switch(self):
        arch = self.settings_arch()
        about = arch.xpath("//div[@id='about']")[0]
        self.assertEqual(about.get("invisible"), "twp_debrand_settings")
        self.assertTrue(about.xpath(".//widget[@name='res_config_edition']"))
        tools = arch.xpath("//widget[@name='res_config_dev_tool']")[0]
        self.assertFalse(hidden(tools), "Developer Tools stay")
        self.assertEqual(next(about.iterancestors("app")).get("name"), "general_settings")
        self.switch(True)
        self.assertTrue(self.env["res.config.settings"].create({}).twp_debrand_settings)
        self.switch(False)
        self.assertFalse(self.env["res.config.settings"].create({}).twp_debrand_settings)

    # Apps: Enterprise apps.

    def app_names(self):
        result = self.Module.with_user(self.admin).web_search_read([], {"name": {}})
        return {record["name"] for record in result["records"]}

    def test_apps_hide_enterprise_when_on(self):
        self.assertTrue(self.to_buy, "base ships Enterprise app records")
        self.switch(True)
        names = self.app_names()
        self.assertFalse(names & set(self.to_buy.mapped("name")))
        self.assertIn("base", names)
        groups = self.Module.with_user(self.admin).web_read_group([], ["state"])["groups"]
        self.assertEqual(sum(g["__count"] for g in groups), self.Module.search_count([("to_buy", "=", False)]))

    def test_apps_off_is_odoos_list(self):
        self.switch(False)
        self.assertLessEqual(set(self.to_buy.mapped("name")), self.app_names())
        groups = self.Module.with_user(self.admin).web_read_group([], ["state"])["groups"]
        self.assertEqual(sum(g["__count"] for g in groups), self.Module.search_count([]))

    def test_category_counters_follow_the_switch(self):
        def total():
            panel = self.Module.with_user(self.admin).search_panel_select_range(
                "category_id", enable_counters=True, search_domain=[],
            )
            return sum(value["__count"] for value in panel["values"])

        self.switch(False)
        odoo_total = total()
        self.switch(True)
        self.assertLess(total(), odoo_total)

    def test_orm_and_update_list_still_see_every_module(self):
        # update_list matches records by search([]); a module it cannot see it
        # creates again. Only the web client's reads are narrowed.
        self.switch(True)
        count = self.Module.search_count([])
        self.assertIn(self.to_buy[0], self.Module.search([]))
        self.assertEqual(self.Module.search([("name", "=", self.to_buy[0].name)]), self.to_buy[0])
        self.Module.update_list()
        self.assertEqual(self.Module.search_count([]), count)
        self.assertEqual(self.Module.search([("to_buy", "=", True)]), self.to_buy)
        self.env.cr.execute("SELECT name FROM ir_module_module GROUP BY name HAVING count(*) > 1")
        self.assertFalse(self.env.cr.fetchall(), "no module may be listed twice")

    # Apps: the store links.

    def test_store_menus_follow_the_switch(self):
        Menu = self.env["ir.ui.menu"].with_user(self.admin)
        apps = self.env.ref("base.menu_apps").id
        stores = {self.env.ref("base.menu_third_party").id, self.env.ref("base.menu_theme_store").id}
        self.switch(False)
        menus = Menu.load_menus(False)
        self.assertLessEqual(stores, set(menus))
        self.assertLessEqual(stores, set(menus[apps]["children"]))
        self.switch(True)
        menus = Menu.load_menus(False)
        self.assertFalse(stores & set(menus))
        self.assertFalse(stores & set(menus[apps]["children"]))
        self.assertIn(self.env.ref("base.menu_module_tree").id, menus[apps]["children"])
        self.switch(False)
        self.assertLessEqual(stores, set(Menu.load_menus(False)), "Odoo's cached menus are left whole")
