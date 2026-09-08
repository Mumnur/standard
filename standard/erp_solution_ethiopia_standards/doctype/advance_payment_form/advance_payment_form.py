# Copyright (c) 2026, ERP Solution Ethiopia PLC and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import flt, money_in_words


class AdvancePaymentForm(Document):
    def validate(self):
        self.calculate_totals()

    def calculate_totals(self):
        grand_total = 0

        for row in self.advance_payment_form_table:
            row.total_amount = flt(row.rate_per_day) * flt(row.no_of_days)
            grand_total += flt(row.total_amount)

        self.grand_total_amount_in_figure = grand_total
        self.grand_total_amount_in_word = money_in_words(
            grand_total,
            frappe.defaults.get_global_default("currency")
        )


@frappe.whitelist()
def get_amount_in_words(amount):
    amount = flt(amount)
    currency = frappe.defaults.get_global_default("currency")
    return money_in_words(amount, currency)