# odoo-backend-branding

Two Odoo 19 Community modules that let a client's admin brand the backend from Settings, inside
their own database, plus small bridges that install themselves when an optional app is present:

| Module | Status | What it does |
|---|---|---|
| `twp_theme_settings` | 0.1, proof stage | Light and dark palettes, any Google Font (downloaded once, served from the database), size, corner radius and density, form width, per-company navbar and button colours and navbar logo, a branded login page, a staging marker on neutralized copies, a per-user dark-mode switch, a live preview card in Settings, and download and load of a look as a file |
| `twp_theme_settings_mail` | 0.1, bridge | Chatter position (Odoo's default, always below, or beside the form from 1200px). Installs itself with Discuss |
| `twp_debrand` | not started | Removes Odoo branding from the tab title, favicon, user menu, login page, emails, portal and Settings |

This repo is the master copy. Releases are copied into each client's code repo, which is that
client's addons path on Oduflow. Design and decisions: ThriveWell's research doc
`work/design/2026-10-08-odoo-look-and-feel-module-research.md`.

## How the theme reaches the screen

* **Compiled, per database.** Settings writes two generated SCSS files as attachments
  (`twp_theme_settings/static/twp_theme.scss` and `..._dark.scss`, paths that exist only in the
  database). `ir.asset` records prepend them to the backend bundles only, so the website, login,
  portal, report and POS bundles never recompile.
* **Runtime, per page load.** The selected company's colours and the staging marker are a small
  `<style>` block rendered into the web client, so switching company needs no recompile.
* **Login page, inline.** The login page loads the frontend bundles, which never carry the theme,
  so the branded page writes its colours and font links into its own `<head>`. It replaces the
  login layout's root (website's, when website is installed) and keeps that root for when the
  branded page is off.
* **Preview, in the browser.** The card at the top of Settings draws a sample list, record and
  login card from the unsaved form. `static/src/js/colors.js` repeats the server's colour maths
  (`models/colors.py` and the palette methods in `models/twp_theme.py`); change one, change the
  other. `TestPreviewParity` runs the JavaScript under Node against the Python.

## Moving a look between databases

Settings > Backend Theme > Copy and reset downloads the saved look as JSON and loads one through a
wizard. The file carries the colours, dark-mode switch, fonts (by name; the loading database
downloads them), size, radius, density, form width, login page with its images, and the chatter
position when the Discuss bridge is installed. A blank setting is `null`, so loading a file gives
exactly the source's look. Staging marking and company colours and logos stay with their database.
A bridge adds its settings to the file by extending `res.config.settings._twp_look_fields`.

## Tests

```
--test-tags /twp_theme_settings            # bundles, generation, the rendered page, login, looks, preview parity
--test-tags /twp_theme_settings_mail       # chatter position reaches the client
--test-tags /twp_theme_settings:TestCompile    # compiles the real bundles; slow
--test-tags twp_network                    # Google Fonts download; needs outbound HTTPS
```

The preview parity test needs `node` on the server's PATH and skips itself without it. The
official `odoo:19.0` image has it.
