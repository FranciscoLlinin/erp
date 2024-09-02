# -*- coding: utf-8 -*-
from odoo import models, api, _
from lxml import etree
from lxml.html import builder as html


class Invite(models.TransientModel):
    _inherit = 'mail.wizard.invite'


    @api.model
    def default_get(self, fields):
        result = super(Invite, self).default_get(fields)
        model = result.get('res_model')
        res_id = result.get('res_id')
        if model == 'crm.lead' and res_id:
            user_name = self.env.user.display_name
            rec = self.env[model].browse(res_id)
            title = rec.display_name
            partner_name = rec.partner_id.name if rec.partner_id else rec.contact_name
            msg_fmt = '{} le invitó a seguir Iniciativa/Oportunidad el documento: {}'.format(user_name, title)            
            if partner_name:
                msg_fmt += ' - {}'.format(partner_name)
            message = html.DIV(
                html.P('Hola,'),
                html.P(msg_fmt)
            )
            result['message'] = etree.tostring(message)
        return result