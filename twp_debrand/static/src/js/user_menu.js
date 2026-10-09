// Odoo's entries are added there; importing it first lets these removals run after.
import "@web/webclient/user_menu/user_menu_items";
import { registry } from "@web/core/registry";
import { session } from "@web/session";

// "My Odoo.com Account" goes. Help opens the admin's support link (the server
// puts it in session.support_url), or goes too when there is none.
const debrand = session.twp_debrand;

if (debrand?.user_menu) {
    const items = registry.category("user_menuitems");
    items.remove("odoo_account");
    if (!debrand.support_url) {
        items.remove("support");
    }
}
