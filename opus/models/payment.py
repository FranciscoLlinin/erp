# -*- coding: utf-8 -*-
from odoo import models, fields, api
import logging
_logger = logging.getLogger(__name__)


class Payment(models.Model):
    _name = 'account.payment'
    _inherit = 'account.payment'

    sent_to_opus = fields.Boolean(string='Sent to OPUS')

    def get_payments_for_invoice(self, invoice_id):
        if invoice_id == 0:
            return False

        query = """
              select invoice.id invoice_id,
                     invoice.move_type inovice_type,
                     invoice.name invoice_number,
                     invoice.state invoice_state,
                     invoice.company_id invoice_company_id,
                     invoice.currency_id invoice_currency_id,
                     0 as invoice_account_id,
                     invoice.opus_payment_type,
                     invoiceLine.id invoice_move_line_id,
                     debits.id debits_id,
                     debits.debit_move_id debits_debit_move_id,
                     debits.credit_move_id debits_credit_move_id,
                     debits.amount debits_amount,
                     debits.debit_amount_currency debits_amount_currency,
                     coalesce(debits.debit_currency_id, invoice.currency_id) debits_currency_id,
                     paymentMoveLine.id payment_move_line_id,
                     payment.id payment_id,
                     payment_move.name payment_name,
                     payment_move.date payment_date,
                     coalesce(payment_move.name, '') payment_move_name,
                     invoice.payment_state payment_state,
                     journal.id journal_id,
                     '' as journal_post_at_bank_rec,
                     company.currency_id  company_currency_id
              from account_move invoice
              join account_move_line invoiceLine on invoice.id = invoiceLine.move_id
              join account_account account on invoiceLine.account_id = account.id
              join account_account_type accountType on account.user_type_id = accountType.id
              join account_partial_reconcile debits on invoiceLine.id = debits.credit_move_id
              join account_move_line paymentMoveLine on debits.debit_move_id = paymentMoveLine.id
              join account_payment payment on paymentMoveLine.payment_id = payment.id
              join account_move payment_move on payment.move_id = payment_move.id
              join account_journal journal on payment_move.journal_id = journal.id
              join res_company company on invoice.company_id = company.id
              where accountType.type in ('receivable', 'payable')
                    and (payment.is_reconciled = 'true' and payment.is_matched = 'true')
                    and invoice.id =  %s;
       """

        self.env.cr.execute(query, (invoice_id,))
        dataset = self.env.cr.dictfetchall()
        return dataset

    def get_payments_for_invoice_by_order_account(self, invoice_id):
        if invoice_id == 0:
            return False

        query = """
              select invoice.id invoice_id,
                     invoice.move_type inovice_type,
                     invoice.name invoice_number,
                     invoice.state invoice_state,
                     invoice.company_id invoice_company_id,
                     invoice.currency_id invoice_currency_id,
                     0 as invoice_account_id,
                     invoice.opus_payment_type,
                     0 as invoice_move_line_id,
                     0 as debits_id,
                     0 as debits_debit_move_id,
                     0 as debits_credit_move_id,
                     invoice.amount_total as debits_amount,
                     invoice.amount_total as debits_amount_currency,
                     invoice.currency_id as debits_currency_id,
                     0 as payment_move_line_id,
                     invoice.id as payment_id,
                     'Pago por cuenta de orden' payment_name,
                     invoice.invoice_date as payment_date,
                     '' as payment_move_name,
                     invoice.payment_state payment_state,
                     0 as journal_id,
                     '' as journal_post_at_bank_rec,
                     company.currency_id  company_currency_id
              from account_move as invoice
              inner join res_company company on invoice.company_id = company.id
              where invoice.payment_state = 'paid'
                    and invoice.id = %s;
        """

        self.env.cr.execute(query, (invoice_id,))
        dataset = self.env.cr.dictfetchall()
        return dataset
