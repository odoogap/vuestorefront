# -*- coding: utf-8 -*-
# Copyright 2023 ODOOGAP/PROMPTEQUATION LDA
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).
import base64
import io
from mimetypes import guess_extension
from PIL import Image, WebPImagePlugin

from odoo import models
from odoo.http import request
from odoo.tools.safe_eval import safe_eval
from odoo.tools.mimetypes import guess_mimetype, get_extension


class IrBinary(models.AbstractModel):
    _inherit = 'ir.binary'

    def _get_image_stream_from(
        self, record, field_name='raw', filename=None, filename_field='name',
        mimetype=None, default_mimetype='image/png', placeholder=None,
        width=0, height=0, crop=False, quality=0,
    ):
        stream = super()._get_image_stream_from(record=record, field_name=field_name, filename=filename, filename_field=filename_field,
                                    mimetype=mimetype, default_mimetype=default_mimetype, placeholder=placeholder,
                                    width=width, height=height, crop=crop, quality=quality)
        if filename and filename.endswith(('jpeg', 'jpg')):
            image_format = 'jpeg'
        else:
            image_format = 'webp'
        if stream.data and width and height:
            image_base64 = stream.data
            img = Image.open(io.BytesIO(image_base64))
            ICP = request.env['ir.config_parameter'].sudo()
            if img.mode != 'RGBA':
                img = img.convert('RGBA')

            # Get background color from context or settings
            try:
                if self.env.context.get('background_rgba'):
                    background_rgba = safe_eval(self.env.context.get('background_rgba'))
                else:
                    background_rgba = safe_eval(ICP.get_param('vsf_image_background_rgba', '(255, 255, 255, 255)'))
            except:
                background_rgba = (66, 28, 82)
            # Create a new background, merge the background with the image centered
            img_w, img_h = img.size
            if image_format == 'jpeg':
                background = Image.new('RGB', (width, height), background_rgba[:3])
            else:
                background = WebPImagePlugin.Image.new('RGBA', (width, height), background_rgba)
            bg_w, bg_h = background.size
            offset = ((bg_w - img_w) // 2, (bg_h - img_h) // 2)
            background.paste(img, offset)

            # Get compression quality from settings
            quality = ICP.get_param('vsf_image_quality', 100)

            stream_image = io.BytesIO()
            if image_format == 'jpeg':
                background.save(stream_image, format=image_format.upper(), subsampling=0)
            else:
                background.save(stream_image, format=image_format.upper(), quality=quality, subsampling=0)

            image_base64 = base64.b64encode(stream_image.getvalue())

            # Response
            stream.data = base64.b64decode(image_base64)
        self._update_download_name(record, stream, filename, field_name, filename_field, f'image/{image_format}', default_mimetype)
        return stream

    def _update_download_name(self, record, stream, filename, field_name, filename_field, mimetype, default_mimetype):
        if stream.type in ('data', 'path'):
            if mimetype:
                stream.mimetype = mimetype
            elif not stream.mimetype:
                if stream.type == 'data':
                    head = stream.data[:1024]
                else:
                    with open(stream.path, 'rb') as file:
                        head = file.read(1024)
                stream.mimetype = guess_mimetype(head, default=default_mimetype)

            if filename:
                stream.download_name = filename
            elif filename_field in record:
                stream.download_name = record[filename_field]
            if not stream.download_name:
                stream.download_name = f'{record._table}-{record.id}-{field_name}'

            stream.download_name = stream.download_name.replace('\n', '_').replace('\r', '_')
            if (not get_extension(stream.download_name)
                and stream.mimetype != 'application/octet-stream'):
                stream.download_name += guess_extension(stream.mimetype) or ''