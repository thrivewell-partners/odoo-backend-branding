import base64

from odoo import http
from odoo.addons.web.controllers import webmanifest
from odoo.http import Stream, request
from odoo.tools.image import ImageProcess

# The sizes pages and the app manifest ask for, and Odoo's own file for each.
ODOO_ICONS = {
    32: "/web/static/img/favicon.ico",
    180: "/web/static/img/odoo-icon-ios.png",
    192: "/web/static/img/odoo-icon-192x192.png",
    512: "/web/static/img/odoo-icon-512x512.png",
}


def icon_png(attachment, size):
    """The icon as a square PNG of the given size, or None for an image Odoo
    cannot process (SVG, WebP)."""
    image = ImageProcess(attachment.raw, verify_resolution=False)
    if not image.image:
        return None
    side = min(image.image.size)
    image.crop_resize(side, side)
    # Browsers and app launchers want the exact size, so a small upload is
    # enlarged rather than left short.
    image.resize(size, size, expand=True)
    return image.image_quality(output_format="PNG")


class DebrandController(http.Controller):
    @http.route("/twp_debrand/icon/<int:size>", type="http", auth="public", methods=["GET"], readonly=True)
    def icon(self, size, unique=None):
        if size not in ODOO_ICONS:
            raise request.not_found()
        attachment = request.env["twp.debrand"].sudo()._icon()
        if not attachment:
            return request.redirect(ODOO_ICONS[size])
        data = icon_png(attachment, size)
        if data is None:
            return attachment._to_http_stream().get_response()
        stream = Stream(
            type="data",
            data=data,
            mimetype="image/png",
            size=len(data),
            download_name=f"icon-{size}.png",
            etag=f"{attachment.checksum}-{size}",
            last_modified=attachment.write_date,
            public=True,
        )
        # The pages ask with ?unique=<checksum>, so that URL never changes content.
        return stream.get_response(immutable=bool(unique))


class WebManifest(webmanifest.WebManifest):
    def _get_webmanifest(self):
        manifest = super()._get_webmanifest()
        Debrand = request.env["twp.debrand"].sudo()
        if Debrand._icon():
            IrHttp = request.env["ir.http"]
            manifest["icons"] = [
                {"src": IrHttp._twp_icon_url(size), "sizes": f"{size}x{size}", "type": "image/png"}
                for size in (192, 512)
            ]
        color = Debrand._param("theme_color")
        if color:
            manifest["theme_color"] = manifest["background_color"] = color
        return manifest

    @http.route()
    def offline(self):
        # Odoo reads its icon from a file (_icon_path), and the scoped app
        # pages open that path too, so the uploaded icon is passed here instead.
        attachment = request.env["twp.debrand"].sudo()._icon()
        data = attachment and icon_png(attachment, 192)
        if not data:
            return super().offline()
        return request.render("web.webclient_offline", {"odoo_icon": base64.b64encode(data)})
