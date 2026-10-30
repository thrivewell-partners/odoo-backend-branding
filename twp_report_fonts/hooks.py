from .models.res_company import FONTS


def _uninstall_hook(env):
    # The company style sheet is an attachment, rewritten only when a company's
    # style is written. Writing every company back to Odoo's fonts rewrites it
    # now, while the heading field still exists; with no heading font the
    # inherited template adds nothing, so the sheet is Odoo's own again.
    companies = env["res.company"].sudo().with_context(active_test=False).search([])
    companies.filtered(lambda c: c.font in FONTS).font = "Lato"
    companies.twp_heading_font = False
