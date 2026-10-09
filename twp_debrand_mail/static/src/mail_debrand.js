import { notificationPermissionService } from "@mail/core/common/notification_permission_service";
import { OutOfFocusService } from "@mail/core/common/out_of_focus_service";
import { MessagingMenu } from "@mail/core/public_web/messaging_menu";
import "@mail/core/web/messaging_menu_patch";

import { _t, appTranslateFn } from "@web/core/l10n/translation";
import { patch } from "@web/core/utils/patch";
import { session } from "@web/session";

// The admin's app name in Discuss's own sentences, from Settings > Branding.
// No name keeps Odoo's wording.
function appName() {
    return session.twp_debrand?.app_name;
}

patch(MessagingMenu.prototype, {
    get installationRequest() {
        const request = super.installationRequest;
        if (appName()) {
            request.displayName = _t("Install %s", appName());
        }
        return request;
    },
});

// The two toasts after the browser's notification prompt. They are matched in
// mail's own translation, which is what the user sees.
const PERMISSION_TOASTS = {
    "Odoo will not send notifications on this device.": (name) =>
        _t("%s will not send notifications on this device.", name),
    "Odoo will send notifications on this device!": (name) =>
        _t("%s will send notifications on this device!", name),
};

patch(notificationPermissionService, {
    async start(env, services) {
        const name = appName();
        if (!name) {
            return super.start(env, services);
        }
        const notification = services.notification;
        const renamed = {
            ...notification,
            add(message, options) {
                for (const [source, rename] of Object.entries(PERMISSION_TOASTS)) {
                    if (String(message) === String(appTranslateFn(source, "mail"))) {
                        message = rename(name);
                    }
                }
                return notification.add(message, options);
            },
        };
        return super.start(env, { ...services, notification: renamed });
    },
});

// A browser notification for a message with no author shows OdooBot's
// transparent picture. With a new avatar under Branding, show that instead.
const ODOO_BOT_ICON = "/mail/static/src/img/odoobot_transparent.png";

patch(OutOfFocusService.prototype, {
    async sendNotification(params) {
        if (session.twp_debrand_bot_avatar && params.icon === ODOO_BOT_ICON && this.store.odoobot) {
            params = { ...params, icon: this.store.odoobot.avatarUrl };
        }
        return super.sendNotification(params);
    },
});
