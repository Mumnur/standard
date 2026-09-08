# -*- coding: utf-8 -*-
# Copyright (c) 2026, muhammed Nurhusien
# For license information, please see license.txt

import frappe
from frappe.utils import flt, cint, getdate, nowdate
from frappe import msgprint, _
from frappe.model.document import Document
import logging

logger = logging.getLogger(__name__)


class ERPBankReconciliation(Document):
	"""
	Bank Reconciliation controller.

	ONE consolidated entrypoint: `sync_reconciliation`. Both the "Get Payment
	Entries" button and the "Update Clearance Status" button (and every
	filter-change auto-refresh) call this single whitelisted method, with a
	flag telling it whether to push clearance changes first. There used to
	be two separate whitelisted methods (get_payment_entries /
	update_clearance_date), and update_clearance_date silently re-called
	get_payment_entries internally - two names doing overlapping work. Now
	there is exactly one public entrypoint and three private helpers, each
	doing one job:

	  sync_reconciliation          - the only whitelisted method the form calls
	    -> _apply_clearance_changes  - writes clearance ticks to source docs
	    -> _refresh_entries          - re-fetches lines & recomputes totals
	         -> _calculate_system_opening_amount

	Journal Entries can touch multiple bank accounts in a single posting, so
	clearance is tracked on the `Journal Entry Account` child row (fields
	`clearance` / `clearance_date`), not on the Journal Entry parent -
	otherwise clearing one bank account's line would clear every bank
	account's line on that same JE. Payment Entry clearance stays on the
	Payment Entry parent, since a Payment Entry only ever involves one bank
	account (paid_from / paid_to).

	Opening / totals model (this is the part that changed):

	  system_opening_amount  = full book balance of the account for every
	                            posted GL Entry dated BEFORE from_date,
	                            regardless of clearance status, PLUS any
	                            "Is Opening" Journal Entry line on this
	                            account regardless of its own posting_date
	                            (opening JEs are structural, not dated
	                            transactions - see _calculate_system_opening_amount).
	                            This is the standard "brought forward"
	                            balance - not a "previously cleared" balance.
	                            "Is Opening" JE lines are also excluded from
	                            the payment_entries table entirely, so they
	                            never show up as a fake reconciling item
	                            (e.g. deposit in transit).
	  total_debit/credit/amount = summed ONLY from rows whose posting_date
	                            falls inside [from_date, to_date]. Rows
	                            "brought forward" from before from_date are
	                            still shown in the table (so they can be
	                            ticked off), but their amounts are already
	                            inside system_opening_amount, so they are
	                            excluded here to avoid double-counting.
	  system_total_amount    = system_opening_amount + total_amount
	                            (i.e. the full book balance as of to_date).
	  deposit_in_transit /
	  outstanding_checks     = summed from every row currently shown as
	                            uncleared (no clearance_date), regardless of
	                            whether it's a current-period row or a
	                            brought-forward row - these are genuine open
	                            reconciling items against the bank statement.

	Persistence: _refresh_entries rebuilds the 'payment_entries' child table
	in memory and, once every field is final, calls self.save() ONCE (only
	if the document already exists in the DB) to persist the child table and
	every scalar total together, atomically. Writing scalar fields
	individually via db_set while leaving the child table unsaved was the
	cause of a real bug: on an already-saved document, the client's
	frm.reload_doc() call right after would silently discard the freshly
	computed child rows and revert to stale data, making changing the date
	range (or new vouchers landing in range) look like they weren't fetched.
	"""

	# ------------------------------------------------------------------ #
	# Public entrypoint - the ONLY method the client script calls
	# ------------------------------------------------------------------ #

	@frappe.whitelist()
	def sync_reconciliation(self, apply_clearance=0):
		"""
		apply_clearance=0 (default): re-fetch entries for the current filters
			and recompute totals. Used by "Get Payment Entries" and by
			filter-change auto-refresh.
		apply_clearance=1: first push clearance ticks from the child table
			back onto the source documents, THEN re-fetch/recompute. Used by
			"Update Clearance Status".
		"""
		skipped_rows = 0

		if cint(apply_clearance):
			if not self.get('payment_entries'):
				msgprint(_("No payment entries to update."))
				return
			if not self.to_date:
				frappe.throw(_("Please set 'To Date' (Reconciled Till Date) before updating clearance."))
			skipped_rows = self._apply_clearance_changes()

		self._refresh_entries()

		if cint(apply_clearance):
			if skipped_rows:
				msgprint(_(
					"Clearance status updated and totals recalculated. "
					"{0} row(s) were skipped because they could not be linked "
					"to a specific ledger line - please refresh and try again."
				).format(skipped_rows))
			else:
				msgprint(_("Clearance status updated and totals recalculated."))

	# ------------------------------------------------------------------ #
	# Private helpers
	# ------------------------------------------------------------------ #

	def _apply_clearance_changes(self):
		"""
		Writes each row's clearance tick back to its source document.
		- Journal Entry rows: written to the specific Journal Entry Account
		  child row (via voucher_detail_no), so clearing one bank account's
		  line on a multi-bank JE doesn't affect the other bank account's
		  line on the same JE.
		- Payment Entry rows: written to the Payment Entry parent.
		Returns the number of rows skipped (rows with no linkable child row).
		"""
		skipped_rows = 0

		try:
			for d in self.get('payment_entries'):
				payment_document = d.get('payment_document')
				payment_entry = d.get('payment_entry')

				if not payment_document or not payment_entry:
					continue

				new_clearance_date = self.to_date if d.get('clearance') else None
				new_clearance_flag = 1 if d.get('clearance') else 0

				if payment_document == "Journal Entry":
					child_row_name = d.get('voucher_detail_no')
					if not child_row_name:
						logger.warning(
							"Skipping JE clearance update: missing voucher_detail_no for %s",
							payment_entry
						)
						skipped_rows += 1
						continue

					frappe.db.set_value(
						"Journal Entry Account", child_row_name,
						{"clearance_date": new_clearance_date, "clearance": new_clearance_flag}
					)
				else:
					frappe.db.set_value(
						payment_document, payment_entry,
						{"clearance_date": new_clearance_date, "clearance": new_clearance_flag}
					)

			return skipped_rows

		except Exception as e:
			logger.exception("Error in _apply_clearance_changes: %s", e)
			frappe.throw(_("Error updating clearance dates: {0}").format(e))

	def _calculate_system_opening_amount(self):
		"""
		System opening amount as of self.from_date: the FULL book balance of
		the bank account - every posted (docstatus=1) GL Entry dated before
		from_date, regardless of whether it has since been cleared - PLUS
		any "Is Opening" Journal Entry line on this account, regardless of
		its own posting_date.

		This intentionally does NOT filter by voucher_type for the "before
		from_date" part. A bank account's opening balance in the books can
		come from any voucher type (Journal Entry, Payment Entry,
		Sales/Purchase Invoice, Bank Entry, etc.) - restricting to just
		JE/PE would silently exclude real transactions and
		understate/overstate the opening balance.

		The "Is Opening" carve-out exists because opening-balance Journal
		Entries are structural (they represent the starting balance, like
		Peachtree's beginning balance) rather than dated transactions. They
		are frequently posted on/after from_date (e.g. at fiscal year
		start), so a plain "posting_date < from_date" filter would miss
		them - and then _refresh_entries would fetch them as an ordinary
		uncleared row, wrongly inflating deposit_in_transit /
		outstanding_checks. Folding them in here, and excluding them from
		_refresh_entries's fetch entirely, keeps them out of the
		reconciling-items list altogether, same as Peachtree does.
		"""
		if not (self.bank_account and self.from_date):
			logger.debug("_calculate_system_opening_amount: missing bank_account or from_date")
			return

		try:
			result = frappe.db.sql("""
				SELECT
					COALESCE(SUM(gle.debit_in_account_currency - gle.credit_in_account_currency), 0) AS balance
				FROM `tabGL Entry` gle
				LEFT JOIN `tabJournal Entry` je
					ON gle.voucher_type = 'Journal Entry' AND gle.voucher_no = je.name
				WHERE gle.account = %(account)s
					AND gle.docstatus = 1
					AND (
						gle.posting_date < %(from)s
						OR (je.is_opening = 'Yes' AND gle.posting_date <= %(to)s)
					)
			""", {
				"account": self.bank_account,
				"from": self.from_date,
				"to": self.to_date
			}, as_dict=True)

			self.system_opening_amount = flt(result[0]['balance']) if result else 0.0

		except Exception as e:
			logger.exception("Error in _calculate_system_opening_amount: %s", e)
			frappe.throw(_("Error calculating system opening amount: {0}").format(e))

	def _refresh_entries(self):
		"""
		Fetches Journal Entry Account rows and Payment Entry rows for the
		bank account / date range, rebuilds the 'payment_entries' child
		table, and recomputes all totals. Journal Entry lines are fetched
		WITHOUT aggregation - one row per Journal Entry Account child row -
		since clearance is tracked per line, not per parent document.

		The table shows three kinds of rows:
		  1. Current-period activity   (posting_date BETWEEN from and to)
		  2. Brought-forward, still uncleared (posted before from_date, no
		     clearance_date yet) - shown so they can be ticked off.
		  3. Brought-forward, cleared during this period (posted before
		     from_date, but clearance_date falls inside from..to) - shown so
		     you can see what just cleared.
		Only rows of kind (1) contribute to total_debit/total_credit/
		total_amount, since kinds (2) and (3) are already included in
		system_opening_amount.
		"""
		if not (self.bank_account and self.from_date and self.to_date):
			logger.debug("_refresh_entries: missing filters - account/from/to")
			return

		try:
			self._calculate_system_opening_amount()

			include_reconciled = bool(self.include_reconciled_entries)
			reconciled_condition_journal = ""
			reconciled_condition_payment = ""
			if not include_reconciled:
				reconciled_condition_journal = "AND (t2.clearance_date IS NULL OR t2.clearance_date = '0000-00-00')"
				reconciled_condition_payment = "AND (clearance_date IS NULL OR clearance_date = '0000-00-00')"

			type_filter = (self.type or "").strip()
			journal_type_condition = ""
			payment_type_condition = ""

			if type_filter == "Debit":
				journal_type_condition = "AND t2.debit_in_account_currency > 0 AND IFNULL(t2.credit_in_account_currency, 0) = 0"
				payment_type_condition = "AND IF(paid_to=%(account)s, received_amount, 0) > 0"
			elif type_filter == "Credit":
				journal_type_condition = "AND IFNULL(t2.credit_in_account_currency, 0) > 0 AND t2.debit_in_account_currency = 0"
				payment_type_condition = "AND IF(paid_from=%(account)s, paid_amount, 0) > 0"

			journal_entries_query = f"""
				SELECT
					"Journal Entry" AS payment_document,
					t1.name AS payment_entry,
					t2.name AS voucher_detail_no,
					t1.cheque_no AS cheque_number,
					t1.cheque_date,
					COALESCE(t2.debit_in_account_currency, 0) AS debit,
					COALESCE(t2.credit_in_account_currency, 0) AS credit,
					t1.posting_date,
					t2.against_account,
					t2.clearance_date,
					t2.account_currency,
					IFNULL(t2.clearance, 0) AS clearance
				FROM
					`tabJournal Entry` t1
					JOIN `tabJournal Entry Account` t2 ON t2.parent = t1.name
				WHERE
					t2.account = %(account)s
					AND t1.docstatus = 1
					AND IFNULL(t1.is_opening, 'No') != 'Yes'
					AND (
						(t1.posting_date BETWEEN %(from)s AND %(to)s)
						OR (t2.clearance_date BETWEEN %(from)s AND %(to)s)
						OR (t1.posting_date < %(from)s AND (t2.clearance_date IS NULL OR t2.clearance_date='0000-00-00'))
					)
					{reconciled_condition_journal}
					{journal_type_condition}
				ORDER BY t1.posting_date ASC, t1.name DESC
			"""

			journal_entries = frappe.db.sql(
				journal_entries_query,
				{"account": self.bank_account, "from": self.from_date, "to": self.to_date},
				as_dict=True
			) or []

			payment_entries_query = f"""
				SELECT
					"Payment Entry" AS payment_document,
					name AS payment_entry,
					NULL AS voucher_detail_no,
					reference_no AS cheque_number,
					reference_date AS cheque_date,
					IF(paid_from=%(account)s, paid_amount, 0) AS credit,
					IF(paid_to=%(account)s, received_amount, 0) AS debit,
					posting_date,
					IFNULL(party, IF(paid_from=%(account)s, paid_to, paid_from)) AS against_account,
					clearance_date,
					IFNULL(clearance, 0) AS clearance,
					IF(paid_to=%(account)s, paid_to_account_currency, paid_from_account_currency) AS account_currency
				FROM `tabPayment Entry`
				WHERE
					(paid_from=%(account)s OR paid_to=%(account)s)
					AND docstatus=1
					AND (
						(posting_date BETWEEN %(from)s AND %(to)s)
						OR (clearance_date BETWEEN %(from)s AND %(to)s)
						OR (posting_date < %(from)s AND (clearance_date IS NULL OR clearance_date='0000-00-00'))
					)
					{reconciled_condition_payment}
					{payment_type_condition}
				ORDER BY posting_date ASC, name DESC
			"""

			payment_entries = frappe.db.sql(
				payment_entries_query,
				{"account": self.bank_account, "from": self.from_date, "to": self.to_date},
				as_dict=True
			) or []

			entries = payment_entries + journal_entries
			entries = sorted(entries, key=lambda k: getdate(k.get('posting_date')) if k.get('posting_date') else getdate(nowdate()))

			self.set('payment_entries', [])
			self.total_debit = 0.0
			self.total_credit = 0.0
			self.total_amount = 0.0
			self.deposit_in_transit = 0.0
			self.outstanding_checks = 0.0

			from_date_obj = getdate(self.from_date)
			to_date_obj = getdate(self.to_date)

			for d in entries:
				original_clearance_date = d.get('clearance_date')
				if original_clearance_date:
					try:
						clear_dt = getdate(original_clearance_date)
						if clear_dt > to_date_obj:
							d['clearance'] = 0
							d['clearance_date'] = None
					except Exception:
						pass

				row = self.append('payment_entries', {})
				row.payment_document = d.get('payment_document')
				row.payment_entry = d.get('payment_entry')
				row.voucher_detail_no = d.get('voucher_detail_no')
				row.cheque_number = d.get('cheque_number')
				row.cheque_date = d.get('cheque_date')
				row.debit = flt(d.get('debit', 0.0))
				row.credit = flt(d.get('credit', 0.0))
				row.posting_date = d.get('posting_date')
				row.against_account = d.get('against_account')
				row.clearance_date = d.get('clearance_date')
				row.clearance = int(d.get('clearance', 0))

				debit_amount = flt(row.debit)
				credit_amount = flt(row.credit)

				# Only current-period activity feeds the totals - anything
				# posted before from_date is already inside
				# system_opening_amount, so adding it here would double-count it.
				row_posting_date = getdate(row.posting_date) if row.posting_date else None
				is_period_entry = row_posting_date is not None and from_date_obj <= row_posting_date <= to_date_obj

				if is_period_entry:
					self.total_debit = flt(self.total_debit) + debit_amount
					self.total_credit = flt(self.total_credit) + credit_amount
					self.total_amount = flt(self.total_amount) + (debit_amount - credit_amount)

				if not row.clearance_date:
					self.deposit_in_transit = flt(self.deposit_in_transit) + debit_amount
					self.outstanding_checks = flt(self.outstanding_checks) + credit_amount

			self.system_total_amount = flt(self.system_opening_amount) + flt(self.total_amount)
			self.unreconciled_amount = flt(self.bank_amount) - flt(self.system_total_amount)
			self.unreconciled_difference = flt(self.bank_amount) - flt(self.outstanding_checks) + flt(self.deposit_in_transit) - flt(self.system_total_amount)

			# IMPORTANT: the child table above (self.set('payment_entries', ...))
			# only exists in memory until it's actually saved. Writing the
			# scalar totals field-by-field via db_set (as this used to do)
			# never touches the child table rows at all - so on an already
			# saved document, the very next frm.reload_doc() on the client
			# would silently discard everything just computed here and fall
			# back to whatever was last actually saved. That's what made
			# changing From/To Date (or new vouchers in range) look like they
			# "didn't fetch" once the document had been saved once.
			#
			# A single self.save() persists the child table AND every scalar
			# field together, atomically, so reload_doc() on the client
			# always reflects what was just computed here. Skipped for a
			# brand-new/unsaved document - there's nothing to persist yet,
			# and the in-memory doc synced back to the client already
			# reflects the fetched rows correctly.
			if not self.is_new():
				self.save(ignore_permissions=True)

			logger.debug("_refresh_entries finished: total_debit=%s total_credit=%s", self.total_debit, self.total_credit)

		except Exception as e:
			logger.exception("Error in _refresh_entries: %s", e)
			frappe.throw(_("Error fetching payment entries: {0}").format(e))


# --- Connection Test Function (kept for JS <-> Python test) ---
@frappe.whitelist()
def check_js_py_connection():
	"""
	A simple whitelisted function to be called from the JS file for sanity testing.
	"""
	frappe.logger().debug("Python method 'check_js_py_connection' was called successfully.")
	return "Success: The Python method was called from JavaScript!"