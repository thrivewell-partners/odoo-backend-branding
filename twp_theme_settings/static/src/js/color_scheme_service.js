import { _t } from "@web/core/l10n/translation";
import { browser } from "@web/core/browser/browser";
import { cookie } from "@web/core/browser/cookie";
import { registry } from "@web/core/registry";
import { session } from "@web/session";
import { user } from "@web/core/user";

// The server decides the scheme when it renders the page (ir.http.color_scheme).
// Odoo's own client code reads the color_scheme cookie for charts, the code
// editor and the colour picker, so keep the cookie in step with that decision.

function darkModeItem(env) {
    return {
        type: "switch",
        id: "twp_dark_mode",
        description: _t("Dark mode"),
        isChecked: session.twp_color_scheme === "dark",
        callback: () => env.services.twp_color_scheme.toggle(),
        sequence: 45,
    };
}

export const twpColorSchemeService = {
    dependencies: ["ui"],
    start(env, { ui }) {
        const rendered = session.twp_color_scheme || "light";
        if (cookie.get("color_scheme") !== rendered) {
            cookie.set("color_scheme", rendered);
        }
        if (session.twp_follow_device) {
            // Browsers that do not send Sec-CH-Prefers-Color-Scheme get one
            // corrective reload the first time the device and page disagree.
            const device = browser.matchMedia("(prefers-color-scheme: dark)").matches
                ? "dark"
                : "light";
            if (device !== rendered) {
                cookie.set("color_scheme", device);
                browser.location.reload();
            }
        }
        if (session.twp_dark_enabled) {
            registry.category("user_menuitems").add("twp_dark_mode", darkModeItem);
        }
        return {
            async toggle() {
                const next = rendered === "dark" ? "light" : "dark";
                ui.block();
                await user.setUserSettings("twp_color_scheme", next);
                cookie.set("color_scheme", next);
                browser.location.reload();
            },
        };
    },
};

registry.category("services").add("twp_color_scheme", twpColorSchemeService);
