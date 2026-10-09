import { user } from "@web/core/user";
import { patch } from "@web/core/utils/patch";
import { NavBar } from "@web/webclient/navbar/navbar";

// The active company's navbar logo, from the company form. Switching company
// reloads the page, so the logo is read once.
patch(NavBar.prototype, {
    get twpNavbarLogo() {
        const company = user.activeCompany;
        if (!company?.twp_navbar_logo) {
            return false;
        }
        return `/web/image/res.company/${company.id}/twp_navbar_logo?unique=${company.twp_navbar_logo}`;
    },
});
