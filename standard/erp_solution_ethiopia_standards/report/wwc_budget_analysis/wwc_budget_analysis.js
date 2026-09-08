// Copyright (c) 2026, Muhammed Nurhusien and contributors
// For license information, please see license.txt

frappe.query_reports["WWC Budget Analysis"] = {
	filters: [

		// =====================================================
		// COMPANY
		// =====================================================

		{
			fieldname: "company",
			label: __("Company"),
			fieldtype: "Link",
			options: "Company",
			default: frappe.defaults.get_user_default("Company"),
			reqd: 1,
		},

		// =====================================================
		// FISCAL YEAR
		// =====================================================

		{
			fieldname: "fiscal_year",
			label: __("Fiscal Year"),
			fieldtype: "Link",
			options: "Fiscal Year",
			default: frappe.defaults.get_user_default("fiscal_year"),

			on_change: function () {

				var fiscal_year =
					frappe.query_report.get_filter_value(
						"fiscal_year"
					);

				if (fiscal_year) {

					frappe.model.with_doc(
						"Fiscal Year",
						fiscal_year,
						function () {

							var fy =
								frappe.model.get_doc(
									"Fiscal Year",
									fiscal_year
								);

							frappe.query_report.set_filter_value(
								"from_date",
								fy.year_start_date
							);

							frappe.query_report.set_filter_value(
								"to_date",
								fy.year_end_date
							);
						}
					);
				}
			},
		},

		// =====================================================
		// ACCOUNT CATEGORY
		//
		// NOTE: ignored server-side when "Show Summary" is on,
		// since Summary mode always shows Admin + Operational
		// side by side. Kept enabled here (not hidden) so the
		// user still sees/can set it for the other modes.
		// =====================================================

		{
			fieldname: "account_category",
			label: __("Account Category"),
			fieldtype: "Select",

			options: [
				"",
				"Operational Expense",
				"Admin Expense",
			].join("\n"),

			default: "",

			description: __(
				"Operational Expense = accounts starting with 5; Admin Expense = accounts starting with 6. Ignored when 'Show Summary' is enabled."
			),

			on_change: function () {

				frappe.query_report.refresh();

			},
		},

		// =====================================================
		// COMPANY BRANCH
		// =====================================================

		{
			fieldname: "company_branch",
			label: __("Company Branch"),
			fieldtype: "MultiSelectList",
			options: "Company Branch",

			get_data: function (txt) {

				return frappe.db.get_link_options(
					"Company Branch",
					txt
				);

			},
		},

		// =====================================================
		// COST CENTER
		// =====================================================

		{
			fieldname: "cost_center",
			label: __("Cost Center"),
			fieldtype: "MultiSelectList",
			options: "Cost Center",

			get_data: function (txt) {

				var company =
					frappe.query_report.get_filter_value(
						"company"
					);

				return frappe.db.get_link_options(
					"Cost Center",
					txt,
					{
						company: company
					}
				);

			},
		},

		// =====================================================
		// PROJECT
		// =====================================================

		{
			fieldname: "project",
			label: __("Project"),
			fieldtype: "MultiSelectList",
			options: "Project",

			get_data: function (txt) {

				return frappe.db.get_link_options(
					"Project",
					txt
				);

			},
		},

		// =====================================================
		// BUDGET MONTH
		// =====================================================

		{
			fieldname: "budget_month",
			label: __("Budget Month"),
			fieldtype: "MultiSelectList",
			options: "Budget Month",

			get_data: function (txt) {

				return frappe.db.get_link_options(
					"Budget Month",
					txt
				);

			},
		},

		// =====================================================
		// FROM DATE
		// =====================================================

		{
			fieldname: "from_date",
			label: __("From Date"),
			fieldtype: "Date",
		},

		// =====================================================
		// TO DATE
		// =====================================================

		{
			fieldname: "to_date",
			label: __("To Date"),
			fieldtype: "Date",
		},

		// =====================================================
		// GROUP BY BRANCH
		// =====================================================

		{
			fieldname: "group_by_branch",
			label: __("Show Branch Columns"),
			fieldtype: "Check",
			default: 0,

			on_change: function () {

				if (
					frappe.query_report.get_filter_value(
						"group_by_branch"
					)
				) {

					frappe.query_report.set_filter_value(
						"group_by_project",
						0
					);

					frappe.query_report.set_filter_value(
						"group_by_summary",
						0
					);

				}

				frappe.query_report.refresh();

			},
		},

		// =====================================================
		// GROUP BY PROJECT
		// =====================================================

		{
			fieldname: "group_by_project",
			label: __("Show Project Columns"),
			fieldtype: "Check",
			default: 0,

			on_change: function () {

				if (
					frappe.query_report.get_filter_value(
						"group_by_project"
					)
				) {

					frappe.query_report.set_filter_value(
						"group_by_branch",
						0
					);

					frappe.query_report.set_filter_value(
						"group_by_summary",
						0
					);

				}

				frappe.query_report.refresh();

			},
		},

		// =====================================================
		// SHOW SUMMARY
		//
		// Branch -> Cost Center tree, Admin vs Operational
		// side by side. Mutually exclusive with the two
		// grouping checks above, and ignores Account Category
		// on the server.
		// =====================================================

		{
			fieldname: "group_by_summary",
			label: __("Show Summary (Branch / Cost Center)"),
			fieldtype: "Check",
			default: 0,

			description: __(
				"Shows Admin and Operational amounts side by side per Branch and Cost Center. Ignores the Account Category filter."
			),

			on_change: function () {

				if (
					frappe.query_report.get_filter_value(
						"group_by_summary"
					)
				) {

					frappe.query_report.set_filter_value(
						"group_by_branch",
						0
					);

					frappe.query_report.set_filter_value(
						"group_by_project",
						0
					);

				}

				frappe.query_report.refresh();

			},
		},

		// =====================================================
		// ONLY OVER BUDGET
		// =====================================================

		{
			fieldname: "only_over_budget",
			label: __("Only Over Budget"),
			fieldtype: "Check",
			default: 0,

			description: __(
				"Show only rows where actual expense exceeds the planned budget."
			),

			on_change: function () {

				frappe.query_report.refresh();

			},
		},

		// =====================================================
		// ONLY WITHOUT PLAN
		// =====================================================

		{
			fieldname: "only_without_plan",
			label: __("Only Without Plan"),
			fieldtype: "Check",
			default: 0,

			description: __(
				"Show only rows with actual expense but no budget plan at all. If both this and 'Only Over Budget' are checked, rows matching either are shown."
			),

			on_change: function () {

				frappe.query_report.refresh();

			},
		},
	],

	// =======================================================
	// FORMATTER
	// =======================================================

	formatter: function (
		value,
		row,
		column,
		data,
		default_formatter
	) {

		value = default_formatter(
			value,
			row,
			column,
			data
		);

		// ---------------------------------------------------
		// Grand Total
		// ---------------------------------------------------

		if (
			data
			&& data.is_total_row
		) {

			value =
				`<span style="font-weight:700;">${value}</span>`;

		}

		// ---------------------------------------------------
		// Summary mode: bold the Branch group rows
		// ---------------------------------------------------

		if (
			data
			&& data.is_group
			&& !data.is_total_row
			&& column.fieldname === "label"
		) {

			value =
				`<span style="font-weight:700;">${value}</span>`;

		}

		// ---------------------------------------------------
		// Unplanned Expense
		//
		// Highlight the account name when actual exists
		// without budget plan.
		// ---------------------------------------------------

		if (
			data
			&& data.is_unplanned
			&& column.fieldname === "account_name"
		) {

			value =
				`<span style="font-weight:600;color:#d9534f;">${value} ⚠️</span>`;

		}

		// ---------------------------------------------------
		// Unplanned Expense (Summary mode: Cost Center label)
		// ---------------------------------------------------

		if (
			data
			&& data.is_unplanned
			&& column.fieldname === "label"
			&& !data.is_group
		) {

			value =
				`<span style="font-weight:600;color:#d9534f;">${value} ⚠️</span>`;

		}

		// ---------------------------------------------------
		// Variance
		// ---------------------------------------------------

		if (
			column.fieldname
			&& column.fieldname.endsWith(
				"_variance"
			)
		) {

			var v =
				data[column.fieldname];

			if (v < 0) {

				value =
					`<span style="color:#d9534f;font-weight:600;">${value}</span>`;

			} else if (v > 0) {

				value =
					`<span style="color:#2b8a3e;font-weight:600;">${value}</span>`;

			}
		}

		// ---------------------------------------------------
		// Utilization
		// ---------------------------------------------------

		if (
			column.fieldname
			&& column.fieldname.endsWith(
				"_utilization"
			)
		) {

			var u =
				data[column.fieldname];

			if (u > 100) {

				value =
					`<span style="color:#d9534f;font-weight:700;">${value} ⚠️</span>`;

			} else if (u >= 90) {

				value =
					`<span style="color:#e6a700;font-weight:600;">${value}</span>`;

			} else {

				value =
					`<span style="color:#2b8a3e;">${value}</span>`;
			}
		}

		return value;
	},

	// =======================================================
	// ONLOAD
	// =======================================================

	onload: function (report) {

		report.page.add_inner_message(

			`<span class="text-muted">
				<i class="fa fa-info-circle"></i>
				${__(
					"Plan is computed from WWC Budgets; Actual is pulled live from GL Entry. For More Info +251 914199288"
				)}
			</span>`

		);

	},

	// =======================================================
	// DATATABLE OPTIONS
	// =======================================================

	get_datatable_options: function (options) {

		return Object.assign(
			options,
			{
				rowHeight: 32,
				cellHeight: 32,
			}
		);

	},
};