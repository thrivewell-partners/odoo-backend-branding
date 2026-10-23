from odoo import SUPERUSER_ID, api

from odoo.addons.twp_debrand_portal.hooks import DEFAULTS_ON


def migrate(cr, version):
    # A database that had the bridge before the switch existed gets it on, as a new install does.
    if not version:
        return
    env = api.Environment(cr, SUPERUSER_ID, {})
    env["twp.debrand"]._switch_on(DEFAULTS_ON)
