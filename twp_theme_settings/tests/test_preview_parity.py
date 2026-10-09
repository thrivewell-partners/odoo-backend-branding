import json
import random
import shutil
import subprocess
import tempfile
from pathlib import Path

from odoo.tests import TransactionCase, tagged
from odoo.tools.misc import file_path

from odoo.addons.twp_theme_settings.models.colors import readable
from odoo.addons.twp_theme_settings.models.twp_theme import PALETTE

from .common import ThemeTestMixin

# Runs colors.js under Node and prints what the preview card would show.
NODE_SCRIPT = """
import { lightPalette, darkPalette, readable, contrastWarnings } from "./colors.mjs";
const cases = JSON.parse(process.argv[2]);
console.log(JSON.stringify(cases.map(([light, dark]) => {
    const lp = lightPalette(light);
    const dp = darkPalette(lp, dark);
    return {
        light: lp, dark: dp,
        link: readable(lp.primary, lp.view), darkLink: readable(dp.primary, dp.view),
        warnings: contrastWarnings(lp, dp).map((w) => [w.scheme, w.pair, w.ratio.toFixed(1)]),
    };
})));
"""
PAIRS = {
    "text on sheets": "text_view",
    "text on page background": "text_bg",
    "button text on primary": "primary",
    "navbar text on navbar": "navbar",
}


def random_hex(rng):
    return "#%06X" % rng.randrange(0x1000000)


@tagged("post_install", "-at_install", "twp_theme")
class TestPreviewParity(ThemeTestMixin, TransactionCase):
    """The preview card in Settings must show the colours the server compiles."""

    def cases(self):
        rng = random.Random(19)
        cases = [
            ({}, {}),
            ({"primary": "#1F5F8B"}, {}),
            ({"navbar": "#16324F", "view": "#1E1E2E"}, {"primary": "#7FB2D9"}),
            ({"primary": "#ffee00", "navbar": "#F5F5F5", "text": "#777777", "bg": "#FFFFFF"}, {"view": "#FAFAFA"}),
            ({"primary": "blue", "navbar": "#12345"}, {"text": "#GGGGGG"}),
        ]
        for _i in range(30):
            light = {key: random_hex(rng) for key in PALETTE if rng.random() < 0.5}
            dark = {key: random_hex(rng) for key in PALETTE if rng.random() < 0.3}
            cases.append((light, dark))
        return cases

    def server(self, light, dark):
        self.set_theme(**{key: light.get(key, False) for key in PALETTE},
                       **{"dark_" + key: dark.get(key, False) for key in PALETTE})
        Theme = self.env["twp.theme"]
        lp, dp = Theme._light_palette(), Theme._dark_palette()
        warnings = []
        for line in Theme._contrast_warnings():
            scheme, rest = line.split(": ", 1)
            name, ratio = rest.split(" is ")
            warnings.append([scheme.lower(), PAIRS[name], ratio.split(":")[0]])
        return {
            "light": lp, "dark": dp,
            "link": readable(lp["primary"], lp["view"]), "darkLink": readable(dp["primary"], dp["view"]),
            "warnings": warnings,
        }

    def test_preview_matches_server(self):
        node = shutil.which("node")
        if not node:
            self.skipTest("Node is not installed, so colors.js cannot be run")
        cases = self.cases()
        with tempfile.TemporaryDirectory() as tmp:
            shutil.copy(file_path("twp_theme_settings/static/src/js/colors.js"), Path(tmp, "colors.mjs"))
            Path(tmp, "check.mjs").write_text(NODE_SCRIPT)
            run = subprocess.run(
                [node, "check.mjs", json.dumps(cases)], cwd=tmp, capture_output=True, text=True, timeout=60,
            )
        self.assertEqual(run.returncode, 0, run.stderr)
        preview = json.loads(run.stdout)
        for (light, dark), shown in zip(cases, preview):
            with self.subTest(light=light, dark=dark):
                self.assertEqual(shown, self.server(light, dark))
