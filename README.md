# odoo-backend-branding

Two Odoo 19 Community modules that let a client's admin brand the backend from Settings, inside
their own database, plus small bridges that install themselves when an optional app is present.
Each module works without the other.

| Module | Status | What it does |
|---|---|---|
| `twp_theme_settings` | 0.1, proof stage | Light and dark palettes, any Google Font (downloaded once, served from the database), size, corner radius and density, form width, per-company navbar and button colours and navbar logo, a branded login page, a staging marker on neutralized copies, a per-user dark-mode switch, a live preview card in Settings, and download and load of a look as a file |
| `twp_theme_settings_mail` | 0.1, bridge | Chatter position (Odoo's default, always below, or beside the form from 1200px). Installs itself with Discuss |
| `twp_debrand` | 0.1, proof stage | Settings > Branding, one switch per place Odoo names itself, all on after install: an app name for the tab, dialogs and installable app, an icon and browser colour, Odoo's user menu items (with an optional support link), the login footer, the "Powered by" badge on portal and website pages, and the edition block, Enterprise upsell settings, Enterprise apps and app store menus |
| `twp_debrand_mail` | 0.1, bridge | The email footer, the weekly update check with odoo.com, and OdooBot's name and avatar. Installs itself with Discuss |
| `twp_debrand_portal` | 0.1, bridge | "Powered by" in the portal's document sidebar. Installs itself with Portal |
| `twp_debrand_payment` | 0.1, bridge | Enterprise-only payment providers. Installs itself with Payments |
| `twp_debrand_theme` | 0.1, bridge | The login switches on the Backend Theme's own login page. Installs itself when both are present |

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

## Dark mode

Odoo 19 Community compiles a dark bundle (`web.assets_web_dark`) but has no switch for it; this
module adds the switch and fills the bundle. Three layers, all compiled from the admin's dark
palette:

* **Variables**, in the generated `..._dark.scss`: the gray scale, white and black swapped, the
  palette, and the colours Odoo fixes for a white page: the success, info, warning and danger text
  shades (list row decorations, `text-*`), inline code, and the navbar counter text.
* **Bootstrap functions**, in `static/src/scss/dark/`: `tint-color` and `shade-color` reversed,
  and dropdowns, tooltips and shadows that Odoo derives from white or black.
* **Components**, in `static/src/scss/dark/components.dark.scss`: tag and colour-badge pills,
  the Discuss unread counters, and links on a state-colour wash. Every text colour here is held
  to 4.5:1; Odoo's backend sets Bootstrap's `$min-contrast-ratio` to 3, so do not use it.

Spreadsheet dashboards stay light: Odoo forces o-spreadsheet to a light scheme in its own dark mode
(`spreadsheet/static/src/o_spreadsheet/o_spreadsheet_extended.dark.scss`).

## How the branding comes off

* **Read on every request.** Each switch is a setting read when a page, email or menu is built, so
  turning one off brings Odoo's back with no upgrade, and uninstalling leaves nothing behind.
* **The app name is Odoo's own** `web.web_app_name` (General Settings' web app name), shown again
  under Branding. Blank keeps "Odoo" everywhere.
* **Enterprise upsells are found by their widget**, not listed: any setting whose field uses
  `upgrade_boolean` is hidden, with any block it leaves empty, so apps installed later are covered.
  Enterprise apps and payment providers are hidden from what the web client reads only; Odoo's own
  module list still sees them, so updating the apps list cannot create duplicates.
* **Emails are cleaned twice**: the two notification layouts drop their footer, and anything else
  sent loses an odoo.com "Odoo" badge link at send time. Links the author typed are kept, and so is
  any other `*.odoo.com` address.
* **Website keeps its own** tab title and favicon on its pages, the login page included.

Not covered yet: OdooBot's onboarding chat text, the digest email's app banner and tips, the
internal-user invitation email's wording, and "Odoo" in Live Chat, Peppol and Calendar texts.

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
--test-tags /twp_theme_settings:TestCompile    # compiles the real bundles, checks dark tags and links; slow
--test-tags twp_network                    # Google Fonts download; needs outbound HTTPS
--test-tags /twp_debrand,/twp_debrand_mail,/twp_debrand_portal,/twp_debrand_payment,/twp_debrand_theme
```

The preview parity test needs `node` on the server's PATH and skips itself without it. The
official `odoo:19.0` image has it.
