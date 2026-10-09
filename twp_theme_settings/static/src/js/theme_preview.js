import { Component, useState } from "@odoo/owl";
import { browser } from "@web/core/browser/browser";
import { _t } from "@web/core/l10n/translation";
import { registry } from "@web/core/registry";
import { isBinarySize } from "@web/core/utils/binary";
import { fileTypeMagicWordMap } from "@web/views/fields/image/image_field";
import { standardWidgetProps } from "@web/views/widgets/standard_widget_props";

import {
    FONT_NAME_RE,
    PALETTE,
    contrastWarnings,
    darkPalette,
    ink,
    isHex,
    lightPalette,
    mix,
    readable,
} from "./colors";

const COLLAPSED_KEY = "twp_theme_settings.preview_collapsed";
const SYSTEM_FONTS = '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Ubuntu, "Noto Sans", Arial, sans-serif';
const PAIRS = {
    text_view: _t("text on sheets"),
    text_bg: _t("text on page background"),
    primary: _t("button text on primary"),
    navbar: _t("navbar text on navbar"),
};
function loadCollapsed() {
    try {
        return browser.localStorage.getItem(COLLAPSED_KEY) === "1";
    } catch {
        return false;
    }
}

/**
 * A sample list, record and login card drawn in the colours, fonts and shape
 * on the Settings form, saved or not. The backend itself changes on Save.
 */
export class ThemePreview extends Component {
    static template = "twp_theme_settings.ThemePreview";
    static props = { ...standardWidgetProps };

    setup() {
        this.state = useState({ scheme: "light", collapsed: loadCollapsed() });
        this.search = useState(this.env.searchState || { value: "" });
    }

    get data() {
        return this.props.record.data;
    }

    get darkEnabled() {
        return Boolean(this.data.twp_dark_enabled);
    }

    get scheme() {
        return this.darkEnabled ? this.state.scheme : "light";
    }

    get palettes() {
        const light = {};
        const dark = {};
        for (const key of PALETTE) {
            light[key] = this.data[`twp_${key}`];
            dark[key] = this.data[`twp_dark_${key}`];
        }
        const lightColors = lightPalette(light);
        return { light: lightColors, dark: darkPalette(lightColors, dark) };
    }

    get warnings() {
        const { light, dark } = this.palettes;
        return contrastWarnings(light, dark)
            .filter((w) => this.darkEnabled || w.scheme === "light")
            .map((w) => ({
                key: `${w.scheme}_${w.pair}`,
                text: _t("%(scheme)s %(pair)s %(ratio)s:1", {
                    scheme: w.scheme === "dark" ? _t("Dark") : _t("Light"),
                    pair: PAIRS[w.pair],
                    ratio: w.ratio.toFixed(1),
                }),
            }));
    }

    fontName(field) {
        const name = (this.data[field] || "").trim().replace(/\s+/g, " ");
        return FONT_NAME_RE.test(name) ? name : "";
    }

    /** A font shows here only once its files are in the page, after Save. */
    fontLoaded(name) {
        return [...document.fonts].some((face) => face.family.replace(/["']/g, "") === name);
    }

    get pendingFonts() {
        const names = [this.fontName("twp_font_body"), this.fontName("twp_font_head")];
        return [...new Set(names.filter((name) => name && !this.fontLoaded(name)))];
    }

    fontStack(name) {
        return name && this.fontLoaded(name) ? `"${name}", ${SYSTEM_FONTS}` : SYSTEM_FONTS;
    }

    get style() {
        const palettes = this.palettes;
        const p = palettes[this.scheme];
        const light = palettes.light;
        const dark = this.scheme === "dark";
        const muted = mix(p.view, p.text, dark ? 0.55 : 0.66);
        const line = mix(p.view, p.text, dark ? 0.12 : 0.15);
        const pressed = mix(p.view, p.primary, 0.1);
        const loginBg = isHex(this.data.twp_login_bg)
            ? this.data.twp_login_bg.toUpperCase()
            : light.navbar;
        const size = parseInt(this.data.twp_font_size) || 14;
        const radius = parseInt(this.data.twp_radius);
        const body = this.fontName("twp_font_body");
        const head = this.fontName("twp_font_head") || body;
        // Every value is a validated hex colour, a number or a checked font name.
        const vars = {
            "--twp-pv-primary": p.primary,
            "--twp-pv-primary-ink": ink(p.primary),
            "--twp-pv-pressed": pressed,
            "--twp-pv-pressed-ink": readable(p.primary, pressed),
            "--twp-pv-navbar": p.navbar,
            "--twp-pv-navbar-ink": ink(p.navbar),
            "--twp-pv-bg": p.bg,
            "--twp-pv-view": p.view,
            "--twp-pv-text": p.text,
            "--twp-pv-muted": muted,
            "--twp-pv-line": line,
            "--twp-pv-link": readable(p.primary, p.view),
            "--twp-pv-size": `${size}px`,
            "--twp-pv-radius": `${Number.isNaN(radius) ? 4 : radius}px`,
            "--twp-pv-pad": this.data.twp_density === "compact" ? "2px" : "5px",
            "--twp-pv-font": this.fontStack(body),
            "--twp-pv-head": this.fontStack(head),
            "--twp-pv-login-bg": loginBg,
            "--twp-pv-login-ink": this.loginImage ? "#FFFFFF" : ink(loginBg),
            // The login page is not themed in dark mode.
            "--twp-pv-login-view": light.view,
            "--twp-pv-login-text": light.text,
            "--twp-pv-login-muted": mix(light.view, light.text, 0.66),
            "--twp-pv-login-line": mix(light.view, light.text, 0.15),
            "--twp-pv-login-primary": light.primary,
            "--twp-pv-login-primary-ink": ink(light.primary),
        };
        for (const key of ["success", "info", "warning", "danger"]) {
            vars[`--twp-pv-${key}`] = p[key];
            vars[`--twp-pv-${key}-ink`] = ink(p[key]);
        }
        return Object.entries(vars)
            .map(([name, value]) => `${name}: ${value}`)
            .join("; ");
    }

    imageUrl(field) {
        const value = this.data[field];
        if (!value || isBinarySize(value) || !/^[A-Za-z0-9+/=]+$/.test(value)) {
            return "";
        }
        const type = fileTypeMagicWordMap[value[0]] || "png";
        return `data:image/${type};base64,${value}`;
    }

    get loginImage() {
        return this.imageUrl("twp_login_background");
    }

    get loginBackgroundStyle() {
        const url = this.loginImage;
        if (!url) {
            return "";
        }
        if (this.data.twp_login_layout === "split") {
            return `background-image: linear-gradient(to top, rgba(0,0,0,.55), rgba(0,0,0,0) 60%), url('${url}')`;
        }
        return `background-image: url('${url}')`;
    }

    get loginLogo() {
        return this.imageUrl("twp_login_logo") || "/web/binary/company_logo";
    }

    setScheme(scheme) {
        this.state.scheme = scheme;
    }

    toggle() {
        this.state.collapsed = !this.state.collapsed;
        try {
            browser.localStorage.setItem(COLLAPSED_KEY, this.state.collapsed ? "1" : "0");
        } catch {
            // Private windows may refuse storage; the choice lasts this visit.
        }
    }
}

// Every field it reads is on the Settings form already.
export const themePreview = { component: ThemePreview };

registry.category("view_widgets").add("twp_theme_preview", themePreview);
