// Copyright (c) 2026, muhammed Nurhusien
// For license information, please see license.txt

frappe.ui.form.on('ERP Bank Reconciliation', {
	refresh(frm) {
		// Frappe's refresh() event can fire more than once per view (e.g.
		// after frm.reload_doc()). Without this, repeated calls to
		// add_custom_button() are what cause "duplicated buttons" - always
		// clear first, then add exactly the buttons we want, once.
		frm.clear_custom_buttons();

		set_buttons(frm);
		render_status_banner(frm);
	},

	setup(frm) {
		frm.add_fetch("bank_account", "account_currency", "account_currency");

		frm.set_query("bank_account", () => ({
			filters: {
				account_type: ["in", ["Bank", "Cash"]],
				is_group: 0
			}
		}));
	},

	// Filter changes just re-fetch - never write, so no confirmation needed.
	bank_account: (frm) => frm.events.sync_reconciliation(frm, false),
	from_date: (frm) => frm.events.sync_reconciliation(frm, false),
	to_date: (frm) => frm.events.sync_reconciliation(frm, false),
	include_reconciled_entries: (frm) => frm.events.sync_reconciliation(frm, false),
	type: (frm) => frm.events.sync_reconciliation(frm, false),

	// Single entrypoint for the whole form - the only place that calls the
	// server. apply_clearance=false: read-only refresh. apply_clearance=true:
	// writes clearance to the source Journal Entry / Payment Entry records.
	sync_reconciliation(frm, apply_clearance) {
		if (!frm.doc.bank_account || !frm.doc.from_date || !frm.doc.to_date) {
			return;
		}

		frm.call({
			method: "sync_reconciliation",
			doc: frm.doc,
			args: { apply_clearance: apply_clearance ? 1 : 0 },
			freeze: true,
			freeze_message: apply_clearance
				? __("Updating clearance status and recalculating totals...")
				: __("Fetching bank transactions...")
		}).then(() => {
			frm.reload_doc();
		}).catch((err) => {
			console.error(err);
			frappe.msgprint({
				title: __('Something went wrong'),
				message: __('Failed to sync reconciliation. See console for details.'),
				indicator: 'red'
			});
		});
	}
});

function set_buttons(frm) {
	// One primary action, always visible: pull the latest entries.
	frm.add_custom_button(__('Refresh Entries'), () => {
		frm.events.sync_reconciliation(frm, false);
	}).addClass('btn-primary');

	// Destructive/write action, grouped under "Actions" - and gated behind
	// an explicit confirmation, since it permanently updates clearance_date
	// on real Journal Entry / Payment Entry records.
	frm.add_custom_button(__('Update Clearance Status'), () => {
		if (!frm.doc.to_date) {
			frappe.msgprint({
				title: __('Missing Date'),
				message: __('Please set the Reconciled Till Date (To Date) before updating clearance.'),
				indicator: 'orange'
			});
			return;
		}

		if (!(frm.doc.payment_entries || []).length) {
			frappe.msgprint({
				title: __('Nothing to Update'),
				message: __('There are no entries in the table yet. Click "Refresh Entries" first.'),
				indicator: 'orange'
			});
			return;
		}

		frappe.confirm(
			__('This will permanently set the clearance date on every Journal Entry / Payment Entry row you\'ve checked or unchecked below, as of {0}. This cannot be undone from this screen. Continue?', [frappe.datetime.str_to_user(frm.doc.to_date)]),
			() => frm.events.sync_reconciliation(frm, true)
		);
	}, __('Actions'));

	// Read-only action, also grouped under "Actions" to keep the toolbar
	// to a single primary button + one dropdown.
	frm.add_custom_button(__('View General Ledger'), () => {
		if (!frm.doc.bank_account) {
			frappe.msgprint(__("Please select a Bank Account first."));
			return;
		}
		frappe.set_route("query-report", "General Ledger", {
			company: frm.doc.company,
			from_date: frm.doc.from_date,
			to_date: frm.doc.to_date,
			account: frm.doc.bank_account,
			group_by: "Group by Voucher (Reference)",
			show_cancelled_entries: 0
		});
	}, __('Actions'));
}

function render_status_banner(frm) {
	// Quick visual read on reconciliation status at the top of the form.
	if (frm.is_new() || frm.doc.unreconciled_difference === undefined || frm.doc.unreconciled_difference === null) {
		return;
	}

	const diff = flt(frm.doc.unreconciled_difference);
	const currency = frm.doc.account_currency;

	if (Math.abs(diff) < 0.005) {
		frm.dashboard.set_headline_alert(
			`<div class="row"><div class="col-xs-12"><i class="fa fa-check-circle text-success"></i> ${__('Reconciled - no outstanding difference')}</div></div>`,
			'green'
		);
	} else {
		frm.dashboard.set_headline_alert(
			`<div class="row"><div class="col-xs-12"><i class="fa fa-exclamation-circle text-warning"></i> ${__('Unreconciled difference')}: ${format_currency(diff, currency)}</div></div>`,
			'orange'
		);
	}
}