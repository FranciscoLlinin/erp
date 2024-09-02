from odoo import http
from odoo.http import content_disposition, request
import base64
import os.path
from odoo.exceptions import except_orm
from odoo import api, fields, models, _


class Controller(http.Controller):

    @http.route('/metodo_valor_ganado', auth="public")
    def descarga_excel(self, **wk):
        ruta = '/var/lib/odoo/.local/share/Odoo/Ecosoft/valor_ganado.xlsx'
        archivo = open(ruta, "rb")
        filename = 'valor_ganado.xlsx'
        return request.make_response(archivo,
                                     [('Content-Type', 'application/vnd.ms-excel'),
                                      ('Content-Disposition', content_disposition(filename))])