"""Small colour helpers shared by the SCSS generator and the runtime layer.

The same arithmetic runs in the Settings preview, so a derived dark colour
looks the same in both places.
"""

import re

HEX_RE = re.compile(r"^#[0-9A-Fa-f]{6}$")


def is_hex(value):
    return bool(value and HEX_RE.match(value))


def rgb(value):
    value = value.lstrip("#")
    return [int(value[i : i + 2], 16) for i in (0, 2, 4)]


def to_hex(channels):
    return "#" + "".join(f"{max(0, min(255, round(c))):02X}" for c in channels)


def mix(a, b, t):
    """Move colour ``a`` towards colour ``b`` by fraction ``t``."""
    x, y = rgb(a), rgb(b)
    return to_hex(xa + (ya - xa) * t for xa, ya in zip(x, y))


def luminance(value):
    def channel(c):
        c /= 255
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4

    r, g, b = (channel(c) for c in rgb(value))
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast(a, b):
    la, lb = luminance(a), luminance(b)
    return (max(la, lb) + 0.05) / (min(la, lb) + 0.05)


LIGHT_INK = "#FFFFFF"
DARK_INK = "#111827"


def ink(background):
    """The text colour, white or near-black, that reads best on ``background``."""
    if contrast(background, LIGHT_INK) >= contrast(background, DARK_INK):
        return LIGHT_INK
    return DARK_INK
