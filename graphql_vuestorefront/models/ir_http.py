# -*- coding: utf-8 -*-
# Copyright 2023 ODOOGAP/PROMPTEQUATION LDA
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

import base64
import codecs
import io

from PIL.WebPImagePlugin import Image
from odoo import api, http, models
from odoo.http import request
from odoo.tools import image_process
from odoo.tools.safe_eval import safe_eval


class Http(models.AbstractModel):
    _inherit = 'ir.http'

    @api.model
    def _content_image(self, xmlid=None, model='ir.attachment', res_id=None, field='datas',
            filename_field='name', unique=None, filename=None, mimetype=None, download=None,
            width=0, height=0, crop=False, quality=0, access_token=None, **kwargs):
        if filename and filename.endswith(('jpeg', 'jpg')):
            request.image_format = 'jpeg'

        return super(Http, self)._content_image(xmlid=xmlid, model=model, res_id=res_id, field=field,
                                                filename_field=filename_field, unique=unique, filename=filename,
                                                mimetype=mimetype, download=download, width=width, height=height,
                                                crop=crop, quality=quality, access_token=access_token, **kwargs)

    @api.model
    def _content_image_get_response(self, status, headers, image_base64, model='ir.attachment',
                                    field='datas', download=None, width=0, height=0, crop=False, quality=0):
        """ Center image in background with color, resize, compress and convert image to webp or jpeg """
        if status == 200 and image_base64 and width and height:
            try:
                # Accepts jpeg and webp, defaults to webp if none found
                if hasattr(request, 'image_format'):
                    image_format = request.image_format
                else:
                    image_format = 'webp'

                width = int(width)
                height = int(height)
                ICP = request.env['ir.config_parameter'].sudo()

                image_base64 = image_process(image_base64, size=(width, height))
                img = Image.open(io.BytesIO(codecs.decode(image_base64, 'base64')))
                if img.mode != 'RGBA':
                    img = img.convert('RGBA')

                # Get background color from settings
                try:
                    background_rgba = safe_eval(ICP.get_param('vsf_image_background_rgba', '(255, 255, 255, 255)'))
                except:
                    background_rgba = (255, 255, 255, 255)

                # Create a new background, merge the background with the image centered
                img_w, img_h = img.size
                if image_format == 'jpeg':
                    background = Image.new('RGB', (width, height), background_rgba[:3])
                else:
                    background = Image.new('RGBA', (width, height), background_rgba)
                bg_w, bg_h = background.size
                offset = ((bg_w - img_w) // 2, (bg_h - img_h) // 2)
                background.paste(img, offset)

                # Get compression quality from settings
                quality = ICP.get_param('vsf_image_quality', 100)

                stream = io.BytesIO()
                if image_format == 'jpeg':
                    background.save(stream, format=image_format.upper(), subsampling=0)
                else:
                    background.save(stream, format=image_format.upper(), quality=quality, subsampling=0)
                image_base64 = base64.b64encode(stream.getvalue())

            except Exception:
                return request.not_found()

            # Replace Content-Type by generating a new list of headers
            new_headers = []
            for index, header in enumerate(headers):
                if header[0] == 'Content-Type':
                    new_headers.append(('Content-Type', f'image/{image_format}'))
                else:
                    new_headers.append(header)

            # Response
            content = base64.b64decode(image_base64)
            new_headers = http.set_safe_image_headers(new_headers, content)
            response = request.make_response(content, new_headers)
            response.status_code = status
            return response

        # Fallback to super function
        return super(Http, self)._content_image_get_response(
            status, headers, image_base64, model=model, field=field, download=download, width=width, height=height,
            crop=crop, quality=quality)
