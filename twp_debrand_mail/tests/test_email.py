import re

from markupsafe import Markup

from odoo.tests import tagged

from odoo.addons.mail.tests.common import MailCommon
from odoo.addons.twp_debrand.models.twp_debrand import PREFIX

ODOO_BADGE = 'href="https://www.odoo.com?utm_source=db&amp;utm_medium=email"'
LAYOUTS = ("mail.mail_notification_layout", "mail.mail_notification_light")


@tagged("post_install", "-at_install", "twp_debrand")
class TestEmail(MailCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.customer = cls.env["res.partner"].create({"name": "Fern Customer", "email": "fern@example.com"})
        cls.record = cls.env["res.partner"].create({"name": "Northfield Supply"})

    def switch(self, on):
        self.env["ir.config_parameter"].sudo().set_param(PREFIX + "email", "True" if on else False)

    def render(self, layout):
        return self.env["mail.render.mixin"].with_context(email_notification_force_footer=True)._render_encapsulate(
            layout, Markup("<p>Your order shipped.</p>"), add_context={"show_unfollow": True}
        )

    def outgoing(self, body_html, body=None):
        mail = self.env["mail.mail"].create({"body_html": body_html, "email_to": "fern@example.com"})
        if body is not None:
            mail.body = body
        return mail._prepare_outgoing_body()

    # The notification layouts

    def test_off_keeps_odoos_footer(self):
        self.switch(False)
        for layout in LAYOUTS:
            html = self.render(layout)
            self.assertIn("Powered by", html, layout)
            self.assertIn(ODOO_BADGE, html, layout)
            # Odoo makes the link absolute when it renders the layout.
            self.assertRegex(html, r'id="mail_unfollow">\s*\| <a href="[^"]*/mail/unfollow"', layout)

    def test_on_drops_the_badge_and_keeps_unfollow(self):
        self.switch(True)
        for layout in LAYOUTS:
            html = self.render(layout)
            self.assertNotIn("Powered by", html, layout)
            self.assertNotIn("odoo.com", html, layout)
            self.assertIn("Your order shipped.", html, layout)
            self.assertRegex(html, r'<span id="mail_unfollow"><a href="[^"]*/mail/unfollow"', layout)
            self.assertEqual(html.count('id="mail_unfollow"'), 1, layout)

    def test_invite_layout_has_one_unfollow(self):
        # mail_notification_invite replaces span#mail_unfollow with its own.
        for on in (False, True):
            self.switch(on)
            html = self.render("mail.mail_notification_invite")
            self.assertEqual("Powered by" in html, not on)
            self.assertEqual(html.count('id="mail_unfollow"'), 1)
            self.assertIn("Not interested by this?", html)

    def test_notification_email(self):
        for on in (False, True):
            self.switch(on)
            with self.mock_mail_gateway():
                self.record.with_user(self.user_employee).with_context(email_notification_force_footer=True).message_post(
                    body=Markup("<p>Your order shipped.</p>"),
                    message_type="comment",
                    subtype_xmlid="mail.mt_comment",
                    partner_ids=self.customer.ids,
                )
            self.assertEqual(len(self._mails), 1)
            body = self._mails[0]["body"]
            self.assertIn("Your order shipped.", body)
            self.assertEqual("Powered by" in body, not on)
            self.assertEqual(ODOO_BADGE in body, not on)

    # Every other email, at send time

    def test_template_badge_is_stripped(self):
        # As auth_signup's templates end, rendered: body_html == body.
        html = (
            '<p>Welcome aboard.</p><div style="color: #555555;">'
            'Powered by <a target="_blank" href="https://www.odoo.com?utm_source=db&amp;utm_medium=auth">Odoo</a></div>'
        )
        self.switch(False)
        self.assertIn("www.odoo.com", self.outgoing(html, html))
        self.switch(True)
        body = self.outgoing(html, html)
        self.assertNotIn("Powered by", body)
        self.assertNotIn("odoo.com", body)
        self.assertIn("<p>Welcome aboard.</p>", body)

    def test_digest_badge_is_stripped(self):
        self.switch(True)
        html = (
            '<div class="by_odoo">Sent by <a href="https://www.odoo.com" target="_blank">'
            '<span class="odoo_link_text">Odoo</span></a> – <a href="/digest/1/unsubscribe">Unsubscribe</a></div>'
        )
        body = self.outgoing(html)
        self.assertNotIn("Sent by", body)
        self.assertNotIn("odoo.com", body)
        self.assertIn("Unsubscribe", body)

    def test_authors_odoo_link_is_kept(self):
        self.switch(True)
        mail = self.env["mail.mail"].create({
            "body": Markup('<p>We moved to <a href="https://www.odoo.com">Odoo</a> last year.</p>'),
            "email_to": "fern@example.com",
        })
        mail.body_html = (
            f'<div>{mail.body}</div><div>Powered by <a href="https://www.odoo.com?utm_source=db">Odoo</a></div>'
        )
        body = mail._prepare_outgoing_body()
        self.assertIn(str(mail.body), body)
        self.assertNotIn("Powered by", body)
        self.assertEqual(len(re.findall("odoo.com", body)), 1)

    def test_other_odoo_hosts_and_links_stay(self):
        self.switch(True)
        html = (
            '<p>Powered by <a href="https://northfield.odoo.com">Odoo</a></p>'
            '<p>Read <a href="https://www.odoo.com/documentation">the documentation</a>.</p>'
        )
        self.assertEqual(self.outgoing(html), html)
