/**
 * The colour arithmetic of models/colors.py and models/twp_theme.py, for the
 * preview card in Settings. It must give the same colours as the server, so
 * any change here is made there too; both test suites check the same values.
 */

export const HEX_RE = /^#[0-9A-Fa-f]{6}$/;
export const FONT_NAME_RE = /^[A-Za-z0-9][A-Za-z0-9 ]{0,59}$/;

export const PALETTE = ["primary", "navbar", "success", "info", "warning", "danger", "bg", "view", "text"];
export const ODOO_LIGHT = {
    primary: "#71639E",
    navbar: "#71639E",
    success: "#28A745",
    info: "#17A2B8",
    warning: "#FFAC00",
    danger: "#DC3545",
    bg: "#F8F9FA",
    view: "#FFFFFF",
    text: "#212529",
};
export const DARK_NEUTRALS = { bg: "#17191F", view: "#20232B", text: "#E5E7EB" };
export const DARK_NAVBAR_BASE = "#0B0D12";
export const LIGHT_INK = "#FFFFFF";
export const DARK_INK = "#111827";

export function isHex(value) {
    return typeof value === "string" && HEX_RE.test(value);
}

function rgb(value) {
    value = value.replace(/^#/, "");
    return [0, 2, 4].map((i) => parseInt(value.slice(i, i + 2), 16));
}

/** Python's round(): halves go to the even neighbour. */
function pyRound(x) {
    const floor = Math.floor(x);
    const diff = x - floor;
    if (diff === 0.5) {
        return floor % 2 === 0 ? floor : floor + 1;
    }
    return Math.round(x);
}

function toHex(channels) {
    return (
        "#" +
        channels
            .map((c) => Math.max(0, Math.min(255, pyRound(c))).toString(16).padStart(2, "0"))
            .join("")
            .toUpperCase()
    );
}

/** Move colour `a` towards colour `b` by fraction `t`. */
export function mix(a, b, t) {
    const x = rgb(a);
    const y = rgb(b);
    return toHex(x.map((xa, i) => xa + (y[i] - xa) * t));
}

export function luminance(value) {
    const channel = (c) => {
        c /= 255;
        return c <= 0.03928 ? c / 12.92 : ((c + 0.055) / 1.055) ** 2.4;
    };
    const [r, g, b] = rgb(value).map(channel);
    return 0.2126 * r + 0.7152 * g + 0.0722 * b;
}

export function contrast(a, b) {
    const la = luminance(a);
    const lb = luminance(b);
    return (Math.max(la, lb) + 0.05) / (Math.min(la, lb) + 0.05);
}

/** The text colour, white or near-black, that reads best on `background`. */
export function ink(background) {
    return contrast(background, LIGHT_INK) >= contrast(background, DARK_INK) ? LIGHT_INK : DARK_INK;
}

/** `color` moved towards white or black until it reads on `background`. */
export function readable(color, background, ratio = 4.5) {
    const target = ink(background) === LIGHT_INK ? LIGHT_INK : "#000000";
    for (let step = 0; step < 11; step++) {
        const candidate = mix(color, target, step / 10);
        if (contrast(candidate, background) >= ratio) {
            return candidate;
        }
    }
    return ink(background);
}

export function deriveDark(light) {
    return {
        primary: mix(light.primary, "#FFFFFF", 0.32),
        navbar: mix(light.navbar, DARK_NAVBAR_BASE, 0.45),
        success: mix(light.success, "#FFFFFF", 0.3),
        info: mix(light.info, "#FFFFFF", 0.3),
        warning: mix(light.warning, "#FFFFFF", 0.25),
        danger: mix(light.danger, "#FFFFFF", 0.3),
        ...DARK_NEUTRALS,
    };
}

/** The hex colours in `values` (key to colour), blank or invalid ones left out. */
export function validColors(values) {
    const result = {};
    for (const key of PALETTE) {
        if (isHex(values[key])) {
            result[key] = values[key].toUpperCase();
        }
    }
    return result;
}

/** As TwpTheme._light_palette, from the colours the admin set. */
export function lightPalette(values) {
    values = validColors(values);
    const palette = { ...ODOO_LIGHT, ...values };
    if ("navbar" in values && !("primary" in values)) {
        palette.primary = values.navbar;
    }
    if ("primary" in values && !("navbar" in values)) {
        palette.navbar = values.primary;
    }
    if (!("text" in values) && ink(palette.view) === LIGHT_INK) {
        palette.text = DARK_NEUTRALS.text;
    }
    return palette;
}

/** As TwpTheme._dark_palette: a blank dark colour is worked out from the light one. */
export function darkPalette(light, darkValues) {
    return { ...deriveDark(light), ...validColors(darkValues) };
}

/** As TwpTheme._contrast_warnings, as data rather than sentences. */
export function contrastWarnings(light, dark) {
    const warnings = [];
    for (const [scheme, palette] of [
        ["light", light],
        ["dark", dark],
    ]) {
        const pairs = [
            ["text_view", palette.text, palette.view],
            ["text_bg", palette.text, palette.bg],
            ["primary", ink(palette.primary), palette.primary],
            ["navbar", ink(palette.navbar), palette.navbar],
        ];
        for (const [pair, fg, bg] of pairs) {
            const ratio = contrast(fg, bg);
            if (ratio < 4.5) {
                // Rounded down, so 4.48 never reads as a passing 4.5.
                warnings.push({ scheme, pair, ratio: Math.floor(ratio * 10) / 10 });
            }
        }
    }
    return warnings;
}
