# -*- coding: utf-8 -*-
from odoo import models, fields, api
import logging
_logger = logging.getLogger(__name__)


class Users(models.Model):
    _name = "res.users"
    _inherit = "res.users"

    def get_assigned_companies(self, user_id):

        sql = """
            select c.id, c.name, c.currency_id, cur.name as currency
            from res_company_users_rel r
            inner join res_company c on c.id = r.cid
            inner join res_currency cur on cur.id = c.currency_id
            where r.user_id = %s;
            """
        user_id_tuple = user_id,
        self.env.cr.execute(sql,
                            user_id_tuple)
        result_set = self.env.cr.dictfetchall()

        return result_set

    def get_companies(self, *args, **kwargs):
        result_set = []
        for company in self.env.companies:
            currency_id = company.currency_id.id
            currency_name = company.currency_id.name
            id = company.id
            name = company.name
            values = {'id': id,
                      'name': name,
                      'currency_id': currency_id,
                      'currency': currency_name}
            result_set.append(values)
        return result_set
