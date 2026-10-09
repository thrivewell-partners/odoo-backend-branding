from odoo import api, models
from odoo.fields import Domain

# Apps > Third-Party Apps and Apps > Theme Store, both links to apps.odoo.com.
STORE_MENUS = ("base.menu_third_party", "base.menu_theme_store")


def hide_enterprise(env, domain, field):
    """``domain``, narrowed to records not sold as Odoo Enterprise when the switch is on.

    Only the web client's own reads go through this. The ORM's search stays
    whole: ``update_list`` looks modules up by ``search([])`` and would create
    a second record for any it could not see, and dependency checks and module
    imports look modules up by name.
    """
    if not env["twp.debrand"]._on("settings"):
        return domain
    return list(Domain.AND([domain or [], [(field, "=", False)]]))


class IrModuleModule(models.Model):
    _inherit = "ir.module.module"

    # Enterprise apps are records Odoo ships with, stamped to_buy and shown in
    # Apps with an Upgrade button. Kanban, list, grouped views and the category
    # counters each read through one of these.

    @api.model
    @api.readonly
    def web_search_read(self, domain, specification, offset=0, limit=None, order=None, count_limit=None):
        domain = hide_enterprise(self.env, domain, "to_buy")
        return super().web_search_read(
            domain, specification, offset=offset, limit=limit, order=order, count_limit=count_limit
        )

    @api.model
    @api.readonly
    def web_read_group(self, domain, groupby, *args, **kwargs):
        domain = hide_enterprise(self.env, domain, "to_buy")
        return super().web_read_group(domain, groupby, *args, **kwargs)

    @api.model
    def search_panel_select_range(self, field_name, **kwargs):
        kwargs["search_domain"] = hide_enterprise(self.env, kwargs.get("search_domain", []), "to_buy")
        return super().search_panel_select_range(field_name, **kwargs)


class IrUiMenu(models.Model):
    _inherit = "ir.ui.menu"

    @api.model
    def load_menus(self, debug):
        # Filtered after Odoo's cached menus, not in _load_menus_blacklist, so
        # the switch is read on every load and needs no cache cleared to flip.
        menus = super().load_menus(debug)
        if not self.env["twp.debrand"]._on("settings"):
            return menus
        hidden = {
            menu.id for xmlid in STORE_MENUS
            if (menu := self.env.ref(xmlid, raise_if_not_found=False))
        }
        if not hidden & menus.keys():
            return menus
        # A new dict: the one from super() is the cached value itself.
        return {
            key: dict(menu, children=[child for child in menu["children"] if child not in hidden])
            for key, menu in menus.items()
            if key not in hidden
        }
