import re

from markupsafe import Markup

from odoo import models

# A link to Odoo's own site. Any other *.odoo.com host is someone's database.
ODOO_LINK = re.compile(
    r"""<a\b[^>]*?\shref\s*=\s*(["'])(?:https?:)?//(?:www\.)?odoo\.com(?:[/?#:][^"']*)?\1[^>]*>(.*?)</a\s*>""",
    re.IGNORECASE | re.DOTALL,
)
TAG = re.compile(r"<[^>]*>")
# What follows a badge: "Powered by Odoo." or "Sent by Odoo - Unsubscribe".
TRAILER = re.compile(r"\.|\s*[|\u2013]")


def strip_powered_by(html):
    """Remove "Powered by Odoo" and "Sent by Odoo" badges from an email.

    A badge is a link to odoo.com whose text is "Odoo" or only a logo. The words
    before it are translated, so they are found by place rather than by text:
    the short phrase between the previous tag and the link. Any other odoo.com
    link is part of a sentence and stays. The rest of the email is untouched,
    byte for byte.
    """
    pieces, pos = [], 0
    for match in ODOO_LINK.finditer(html):
        if TAG.sub("", match.group(2)).strip().lower() not in ("", "odoo"):
            continue
        start, end = match.start(), match.end()
        lead_start = max(html.rfind(">", pos, start) + 1, pos)
        lead = html[lead_start:start]
        words = lead.strip()
        if words and len(words) <= 30 and not any(c in words for c in ".!?:"):
            start = lead_start + len(lead) - len(lead.lstrip())
            trailer = TRAILER.match(html, end)
            if trailer:
                end = trailer.end()
        pieces.append(html[pos:start])
        pos = end
    if not pieces:
        return html
    pieces.append(html[pos:])
    return "".join(pieces)


class MailMail(models.Model):
    _inherit = "mail.mail"

    def _prepare_outgoing_body(self):
        # The notification layouts drop the badge themselves. This catches every
        # other template: sign-up, digest, live chat and the rest.
        body = super()._prepare_outgoing_body()
        if not body or not self.env["twp.debrand"]._on("email"):
            return body
        # What the author wrote is theirs, Odoo links included. A mail built from
        # a template has body == body_html, and then the whole of it is template.
        keep = str(self.body or "")
        if keep and keep != self.body_html and keep in body:
            result = keep.join(strip_powered_by(part) for part in body.split(keep))
        else:
            result = strip_powered_by(body)
        return Markup(result) if isinstance(body, Markup) else result
