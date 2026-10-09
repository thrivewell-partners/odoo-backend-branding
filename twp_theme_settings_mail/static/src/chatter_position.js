import { SIZES } from "@web/core/ui/ui_service";
import { useService } from "@web/core/utils/hooks";
import { patch } from "@web/core/utils/patch";
import { session } from "@web/session";
import { FormCompiler } from "@web/views/form/form_compiler";
import { FormController } from "@web/views/form/form_controller";
import { FormRenderer } from "@web/views/form/form_renderer";

// The admin's chatter position, from Settings > Backend Theme > Layout.
//
// Odoo 19 puts the chatter beside the form from the XXL breakpoint (1400px)
// and decides it in three places: the renderer's mailLayout, the controller's
// o_xxl_form_view class and the flex direction compiled into the form. All
// three follow mailLayout here. A document preview (vendor bills) keeps
// Odoo's rule and still needs XXL.

const XXL_CLASS = "o_xxl_form_view h-100";
const SIDE_BY_SIDE = ["SIDE_CHATTER", "EXTERNAL_COMBO_XXL", "COMBO"];

function chatterAside(size) {
    switch (session.twp_chatter_position) {
        case "bottom":
            return false;
        case "side":
            return size >= SIZES.XL;
        default:
            return size >= SIZES.XXL;
    }
}

export function mailLayout({ size, hasChatter, hasFile, hasExternalWindow, hasAttachmentContainer }) {
    const aside = chatterAside(size);
    if (hasExternalWindow && hasFile && hasAttachmentContainer) {
        return aside ? "EXTERNAL_COMBO_XXL" : "EXTERNAL_COMBO";
    }
    if (hasChatter) {
        if (size >= SIZES.XXL && hasAttachmentContainer && hasFile) {
            return "COMBO";
        }
        return aside ? "SIDE_CHATTER" : "BOTTOM_CHATTER";
    }
    return "NONE";
}

export function isSideBySide(layout, size) {
    return SIDE_BY_SIDE.includes(layout) || (layout === "NONE" && size >= SIZES.XXL);
}

function hasFile(mailStore, record) {
    if (!mailStore || !record.resId) {
        return false;
    }
    const thread = mailStore.Thread.insert({ id: record.resId, model: record.resModel });
    return thread.attachmentsInWebClientView.length > 0;
}

patch(FormRenderer.prototype, {
    mailLayout(hasAttachmentContainer) {
        return mailLayout({
            size: this.uiService.size,
            hasChatter: !!this.mailStore,
            hasFile: this.hasFile(),
            hasExternalWindow: !!this.mailPopoutService.externalWindow,
            hasAttachmentContainer,
        });
    },
    twpSideBySide(hasAttachmentContainer) {
        return isSideBySide(this.mailLayout(hasAttachmentContainer), this.uiService.size);
    },
});

patch(FormCompiler.prototype, {
    compileForm(el, params) {
        const form = super.compileForm(el, params);
        const hasPreview = Boolean(el.querySelector("div.o_attachment_preview"));
        const classes = form.getAttribute("t-attf-class");
        const xxlTest = `__comp__.uiService.size < ${SIZES.XXL}`;
        if (classes && classes.includes(xxlTest)) {
            form.setAttribute(
                "t-attf-class",
                classes.replace(xxlTest, `!__comp__.twpSideBySide(${hasPreview})`)
            );
        }
        return form;
    },
});

patch(FormController.prototype, {
    setup() {
        super.setup(...arguments);
        if (this.env.services["mail.popout"]) {
            this.twpPopout = useService("mail.popout");
        }
    },
    get className() {
        const result = super.className;
        const size = this.ui.size;
        if (size <= SIZES.XS || this.env.inDialog) {
            return result;
        }
        delete result[XXL_CLASS];
        const hasAttachmentContainer = Boolean(
            this.archInfo.xmlDoc?.querySelector("div.o_attachment_preview")
        );
        const layout = mailLayout({
            size,
            hasChatter: !!this.mailStore,
            hasFile: hasAttachmentContainer && hasFile(this.mailStore, this.model.root),
            hasExternalWindow: !!this.twpPopout?.externalWindow,
            hasAttachmentContainer,
        });
        if (isSideBySide(layout, size)) {
            result[XXL_CLASS] = true;
        }
        return result;
    },
});
