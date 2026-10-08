# odoo-backend-branding

Two Odoo 19 Community modules that let a client's admin brand the backend from Settings, inside
their own database:

| Module | Status | What it does |
|---|---|---|
| `twp_theme_settings` | 0.1, proof stage | Light and dark palettes, any Google Font (downloaded once, served from the database), size and corner radius, per-company navbar and button colours, a staging marker on neutralized copies, and a per-user dark-mode switch |
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

## Tests

```
--test-tags /twp_theme_settings            # bundles, generation, the rendered page
--test-tags /twp_theme_settings:TestCompile    # compiles the real bundles; slow
--test-tags twp_network                    # Google Fonts download; needs outbound HTTPS
```
