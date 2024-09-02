# -*- coding: utf-8 -*-
from odoo import models, api, _
from lxml import etree
from lxml.html import builder as html


class Invite(models.TransientModel):
    _inherit = 'mail.wizard.invite'

    def _get_partner_name_str(self, rec):
        try:
            if rec.partner_id and rec.partner_id.name:
                partner_name = rec.partner_id.name
            elif rec.contact_name:
                partner_name = rec.contact_name
            elif rec.contact:
                partner_name = rec.contact
            else:
                partner_name = ''
        except AttributeError:
            partner_name = ''
        return '{} - '.format(partner_name) if partner_name else ''    


    @api.model
    def default_get(self, fields):
        result = super(Invite, self).default_get(fields)
        model = result.get('res_model')
        res_id = result.get('res_id')
        if model == 'crm.lead' and res_id:
            user_name = self.env.user.display_name
            rec = self.env[model].browse(res_id)
            title = rec.display_name
            partner_name = self._get_partner_name_str(rec)      
            msg_fmt = '{} le invitó a seguir Iniciativa/Oportunidad el documento: {}{}'.format(user_name, partner_name, title)    
            message = html.DIV(
                html.P('Hola,'),
                html.P(msg_fmt)
            )
            result['message'] = etree.tostring(message)
        return result
        
    def add_followers(self):
        """ Inherited if inviting for crm.lead so we can override the email subject. """        
        if not self.filtered(lambda r: r.res_model == 'crm.lead'):
            return super(Invite, self).add_followers()
            
        email_from = self.env['mail.message']._get_default_from()
        for wizard in self:
            Model = self.env[wizard.res_model]
            document = Model.browse(wizard.res_id)

            # filter partner_ids to get the new followers, to avoid sending email to already following partners
            new_partners = wizard.partner_ids - document.message_partner_ids
            new_channels = wizard.channel_ids - document.message_channel_ids
            document.message_subscribe(new_partners.ids, new_channels.ids)
            model_name = self.env['ir.model']._get(wizard.res_model).display_name
            # send an email if option checked and if a message exists (do not send void emails)
            if wizard.send_mail and wizard.message and not wizard.message == '<br>':  # when deleting the message, cleditor keeps a <br>      
                if wizard.res_model == 'crm.lead':
                    partner_name = self._get_partner_name_str(document)
                else:
                    partner_name = ''
                message = self.env['mail.message'].create({
                    'subject': _('Invitation to follow %s: %s%s') % (model_name, partner_name, document.name_get()[0][1]),
                    'body': wizard.message,
                    'record_name': document.name_get()[0][1],
                    'email_from': email_from,
                    'reply_to': email_from,
                    'model': wizard.res_model,
                    'res_id': wizard.res_id,
                    'no_auto_thread': True,
                    'add_sign': True,
                })
                partners_data = []
                recipient_data = self.env['mail.followers']._get_recipient_data(document, False, pids=new_partners.ids)
                for pid, cid, active, pshare, ctype, notif, groups in recipient_data:
                    pdata = {'id': pid, 'share': pshare, 'active': active, 'notif': 'email', 'groups': groups or []}
                    if not pshare and notif:  # has an user and is not shared, is therefore user
                        partners_data.append(dict(pdata, type='user'))
                    elif pshare and notif:  # has an user and is shared, is therefore portal
                        partners_data.append(dict(pdata, type='portal'))
                    else:  # has no user, is therefore customer
                        partners_data.append(dict(pdata, type='customer'))
                self.env['res.partner'].with_context(auto_delete=True)._notify(
                    message, partners_data, document,
                    force_send=True, send_after_commit=False)
                message.unlink()
        return {'type': 'ir.actions.act_window_close'}
