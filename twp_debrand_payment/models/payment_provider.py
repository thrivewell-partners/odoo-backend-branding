from odoo import api, models

from odoo.addons.twp_debrand.models.ir_module_module import hide_enterprise


class PaymentProvider(models.Model):
    _inherit = "payment.provider"

    # Providers whose module is sold as Odoo Enterprise (SEPA Direct Debit) carry
    # an Enterprise badge and an Upgrade button. They go under the same switch as
    # Enterprise apps, and only from the web client's reads, as in Apps.

    @api.model
    @api.readonly
    def web_search_read(self, domain, specification, offset=0, limit=None, order=None, count_limit=None):
        domain = hide_enterprise(self.env, domain, "module_to_buy")
        return super().web_search_read(
            domain, specification, offset=offset, limit=limit, order=order, count_limit=count_limit
        )

    @api.model
    @api.readonly
    def web_read_group(self, domain, groupby, *args, **kwargs):
        domain = hide_enterprise(self.env, domain, "module_to_buy")
        return super().web_read_group(domain, groupby, *args, **kwargs)
