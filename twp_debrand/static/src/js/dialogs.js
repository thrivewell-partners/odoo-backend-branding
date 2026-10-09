import { Dialog } from "@web/core/dialog/dialog";
import {
    ErrorDialog,
    RedirectWarningDialog,
    RPCErrorDialog,
    SessionExpiredDialog,
    WarningDialog,
} from "@web/core/errors/error_dialogs";
import { _t } from "@web/core/l10n/translation";
import { registerTemplateExtension } from "@web/core/templates";
import { patch } from "@web/core/utils/patch";
import { session } from "@web/session";

// Dialogs name the product: "Odoo" as the default title, "Odoo Server Error",
// "Odoo Warning", "Odoo Session Expired". With an app name set in Settings,
// it replaces the word and the rest of each title stays (and stays translated).
const appName = session.twp_debrand?.app_name;
const rename = (text) => text && String(text).replace(/\bOdoo\b/g, () => appName);

if (appName) {
    patch(Dialog.defaultProps, { title: appName });

    // The error dialogs show their title in the technical details.
    patch(ErrorDialog.prototype, {
        setup() {
            super.setup(...arguments);
            this.title = rename(this.constructor.title);
        },
    });
    patch(RPCErrorDialog.prototype, {
        inferTitle() {
            const before = this.title;
            super.inferTitle();
            if (this.title !== before) {
                this.title = rename(this.title);
            }
        },
    });
    patch(WarningDialog.prototype, {
        inferTitle() {
            return rename(super.inferTitle());
        },
    });
    patch(RedirectWarningDialog.prototype, {
        setup() {
            super.setup(...arguments);
            this.title = rename(this.title);
        },
    });

    // This one has its title and message in the template.
    patch(SessionExpiredDialog.prototype, {
        setup() {
            super.setup(...arguments);
            this.twpTitle = rename(_t("Odoo Session Expired"));
            this.twpMessage = rename(
                _t("Your Odoo session expired. The current page is about to be refreshed.")
            );
        },
    });
    registerTemplateExtension(
        "web.SessionExpiredDialog",
        "/twp_debrand/static/src/js/dialogs.js",
        `<t t-inherit="web.SessionExpiredDialog" t-inherit-mode="extension">
            <xpath expr="//Dialog" position="attributes">
                <attribute name="title.translate"/>
                <attribute name="title">twpTitle</attribute>
            </xpath>
            <xpath expr="//div[@role='alert']/p" position="replace">
                <p class="text-prewrap" t-esc="twpMessage"/>
            </xpath>
        </t>`
    );
}
