import { titleService } from "@web/core/browser/title_service";
import { patch } from "@web/core/utils/patch";
import { session } from "@web/session";

// A tab with no page name is called "Odoo". With an app name set in Settings,
// it is called that instead.
const appName = session.twp_debrand?.app_name;

if (appName) {
    patch(titleService, {
        start() {
            const title = super.start(...arguments);
            const rename = () => {
                if (!Object.keys(title.getParts()).length) {
                    document.title = document.title.replace(/Odoo$/, () => appName);
                }
            };
            for (const method of ["setParts", "setCounters"]) {
                const original = title[method];
                title[method] = (...args) => {
                    original(...args);
                    rename();
                };
            }
            return title;
        },
    });
}
