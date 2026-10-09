from odoo import models


class PublisherWarrantyContract(models.AbstractModel):
    _inherit = "publisher_warranty.contract"

    def update_notification(self, cron_mode=True):
        # The weekly check posts the user count, installed apps and company
        # details to odoo.com. The cron stays; it just does nothing while this is on.
        if self.env["twp.debrand"]._on("phone_home"):
            return True
        return super().update_notification(cron_mode=cron_mode)
