# -*- coding: utf-8 -*-
from odoo import models, api
from odoo.tools.translate import _

ODOO_USERS = [3,2]

class CrmLead(models.Model):
    _name = "crm.lead"
    _inherit = 'crm.lead' 
    
    @api.returns('mail.message', lambda value: value.id)
    def message_post(self, **kwargs):
        if not kwargs.get('partner_ids', []):
            follwers = self.message_partner_ids.ids
            for u in ODOO_USERS:
                if u in follwers:
                    follwers.remove(u)
            if self._uid in follwers:
                follwers.remove(self._uid)
            kwargs['partner_ids']=follwers
        return super(CrmLead, self.with_context(mail_post_autofollow=True)).message_post(**kwargs)


    def _notify_get_groups(self, message, groups):
        """ Handle salesman recipients that can convert leads into opportunities
        and set opportunities as won / lost. """
        groups = super(CrmLead, self)._notify_get_groups(message, groups)

        self.ensure_one()
        if self.type == 'lead':
            convert_action = self._notify_get_action_link('controller', controller='/lead/convert')
            salesman_actions = [{'url': convert_action, 'title': _('Convert to opportunity')}]
        else:
            won_action = self._notify_get_action_link('controller', controller='/lead/case_mark_won')
            lost_action = self._notify_get_action_link('controller', controller='/lead/case_mark_lost')
            salesman_actions = [
                {'url': won_action, 'title': _('Won')},
                {'url': lost_action, 'title': _('Lost')}]

        if self.team_id:
            salesman_actions.append({'url': self._notify_get_action_link('view', res_id=self.team_id.id, model=self.team_id._name), 'title': _('Sales Team Settings')})

        salesman_group_id = self.env.ref('sales_team.group_sale_salesman').id
        new_group = (
            'group_sale_salesman', lambda pdata: pdata['type'] == 'user' , {
                'actions': salesman_actions,
            })

        return [new_group] + groups