# Copyright (c) 2026, Muhammed Nurhusien and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import flt, getdate, date_diff, cint


ADMIN_PREFIX = "6"
OPERATIONAL_PREFIX = "5"


# ============================================================
# EXECUTE
# ============================================================

def execute(filters=None):

	filters = prepare_filters(filters or {})

	# --------------------------------------------------------
	# SUMMARY MODE (Branch / Cost Center x Admin / Operational)
	#
	# This mode always looks at BOTH Admin (6) and Operational (5)
	# accounts side by side, so the "Account Category" filter is
	# intentionally ignored here.
	# --------------------------------------------------------

	if filters.get("group_by_summary"):

		return get_summary_report(filters)

	# --------------------------------------------------------
	# Get planned budgets
	# --------------------------------------------------------

	planned_raw, planned_accounts = get_planned_budgets(
		filters
	)

	# --------------------------------------------------------
	# Get actual expenses
	#
	# IMPORTANT:
	# We intentionally DO NOT restrict actual expenses
	# to planned accounts.
	#
	# This allows unplanned Expense accounts to appear.
	# --------------------------------------------------------

	actual_raw = get_actual_costs_from_gl(filters)

	# --------------------------------------------------------
	# Get accounts having actual expenses
	# --------------------------------------------------------

	actual_accounts = {
		key[0]
		for key in actual_raw.keys()
	}

	# --------------------------------------------------------
	# Combine planned + actual accounts
	# --------------------------------------------------------

	all_accounts = sorted(
		set(planned_accounts) | actual_accounts
	)

	if not all_accounts:
		return [], [], None, None, []

	# ========================================================
	# PROJECT MODE
	# ========================================================

	if filters.get("group_by_project"):

		columns = get_project_columns()

		data, summary = get_project_summary_data(
			planned_raw,
			actual_raw,
			filters
		)

		chart = get_project_chart(data)

		return (
			columns,
			data,
			None,
			chart,
			summary
		)

	# ========================================================
	# ACCOUNT / BRANCH MODE
	# ========================================================

	planned_map = aggregate_account_branch(
		planned_raw
	)

	actual_map = aggregate_account_branch(
		actual_raw
	)

	branches = get_distinct_values(
		planned_raw,
		actual_raw,
		index=1
	)

	columns = get_columns(
		filters,
		branches
	)

	data, summary = get_report_data_and_summary(
		filters,
		all_accounts,
		branches,
		planned_map,
		actual_map
	)

	chart = get_chart(data)

	return (
		columns,
		data,
		None,
		chart,
		summary
	)


# ============================================================
# FILTER HELPERS
# ============================================================

def as_list(value):

	"""
	Normalize a MultiSelectList filter value.

	Supports:
	- Python list
	- JSON string
	- Single value
	"""

	if not value:
		return []

	if isinstance(value, list):
		return value

	if isinstance(value, str):

		if value.startswith("["):

			try:

				parsed = frappe.parse_json(value)

				if isinstance(parsed, list):
					return parsed

			except Exception:
				pass

		return [value]

	return [value]


def prepare_filters(filters):

	filters = frappe._dict(filters)

	# --------------------------------------------------------
	# Fiscal Year
	# --------------------------------------------------------

	if (
		filters.get("fiscal_year")
		and (
			not filters.get("from_date")
			or not filters.get("to_date")
		)
	):

		fy = frappe.db.get_value(
			"Fiscal Year",
			filters["fiscal_year"],
			[
				"year_start_date",
				"year_end_date"
			],
			as_dict=True
		)

		if fy:

			filters["from_date"] = (
				filters.get("from_date")
				or fy.year_start_date
			)

			filters["to_date"] = (
				filters.get("to_date")
				or fy.year_end_date
			)

	# --------------------------------------------------------
	# MultiSelect filters
	# --------------------------------------------------------

	filters["company_branch_list"] = as_list(
		filters.get("company_branch")
	)

	filters["project_list"] = as_list(
		filters.get("project")
	)

	filters["budget_month_list"] = as_list(
		filters.get("budget_month")
	)

	# --------------------------------------------------------
	# Account Category
	#
	# Operational Expense = Account starts with 5
	# Admin Expense       = Account starts with 6
	# All                 = no account restriction
	#
	# NOTE: this restriction is ignored in Summary mode, since
	# Summary mode always shows Admin and Operational side by side.
	# --------------------------------------------------------

	account_category = filters.get(
		"account_category"
	)

	if account_category in (
		"Operational Expense",
		"Operational"
	):

		filters["account_prefix"] = OPERATIONAL_PREFIX

	elif account_category in (
		"Admin Expense",
		"Administration Expense",
		"Admin"
	):

		filters["account_prefix"] = ADMIN_PREFIX

	else:

		filters["account_prefix"] = None

	# --------------------------------------------------------
	# Cost Center
	# --------------------------------------------------------

	cost_centers = as_list(
		filters.get("cost_center")
	)

	if cost_centers:

		expanded = set()

		lft_rgt_rows = frappe.db.get_all(
			"Cost Center",
			filters={
				"name": [
					"in",
					cost_centers
				]
			},
			fields=[
				"name",
				"lft",
				"rgt"
			]
		)

		for cc in lft_rgt_rows:

			if cc.lft and cc.rgt:

				children = frappe.db.get_all(
					"Cost Center",
					filters={
						"lft": [
							">=",
							cc.lft
						],
						"rgt": [
							"<=",
							cc.rgt
						]
					},
					pluck="name"
				)

				expanded.update(children)

			else:

				expanded.add(cc.name)

		filters["cost_center_list"] = sorted(
			expanded
		)

	else:

		filters["cost_center_list"] = []

	# --------------------------------------------------------
	# Row-level budget filters
	#
	# only_over_budget  -> account/branch/cost-center has a plan
	#                      AND actual exceeds that plan
	# only_without_plan -> account/branch/cost-center has actual
	#                      expense but no plan at all
	#
	# If both are checked, rows matching EITHER condition are kept.
	# --------------------------------------------------------

	filters["only_over_budget"] = cint(
		filters.get("only_over_budget")
	)

	filters["only_without_plan"] = cint(
		filters.get("only_without_plan")
	)

	filters["group_by_summary"] = cint(
		filters.get("group_by_summary")
	)

	return filters


def row_matches_budget_filters(
	filters,
	plan,
	actual,
	is_unplanned
):

	"""
	Generic row-level filter used by the account/branch mode,
	the project mode and the summary mode.

	Returns True when the row should be KEPT.
	"""

	only_over_budget = filters.get(
		"only_over_budget"
	)

	only_without_plan = filters.get(
		"only_without_plan"
	)

	if (
		not only_over_budget
		and not only_without_plan
	):

		return True

	plan = flt(plan)
	actual = flt(actual)

	is_over_budget = (
		plan > 0
		and actual > plan
	)

	if (
		only_over_budget
		and is_over_budget
	):

		return True

	if (
		only_without_plan
		and is_unplanned
	):

		return True

	return False


# ============================================================
# ACCOUNT COLUMNS
# ============================================================

def get_columns(filters, branches):

	columns = [

		{
			"label": _("Budget Account"),
			"fieldname": "account",
			"fieldtype": "Link",
			"options": "Account",
			"width": 220,
		},

		{
			"label": _("Account Name"),
			"fieldname": "account_name",
			"fieldtype": "Data",
			"width": 180,
		},
	]

	group_by_branch = filters.get(
		"group_by_branch"
	)

	if (
		group_by_branch
		and branches
	):

		for branch in branches:

			branch_key = frappe.scrub(
				branch
			)

			columns.extend(
				[
					{
						"label": _(
							"{0} (Plan)"
						).format(branch),

						"fieldname":
							f"{branch_key}_plan",

						"fieldtype":
							"Currency",

						"options":
							"Company:company:default_currency",

						"width": 130,
					},

					{
						"label":
							_("Actual"),

						"fieldname":
							f"{branch_key}_actual",

						"fieldtype":
							"Currency",

						"options":
							"Company:company:default_currency",

						"width": 130,
					},

					{
						"label":
							_("Variance"),

						"fieldname":
							f"{branch_key}_variance",

						"fieldtype":
							"Currency",

						"options":
							"Company:company:default_currency",

						"width": 130,
					},

					{
						"label":
							_("Util %"),

						"fieldname":
							f"{branch_key}_utilization",

						"fieldtype":
							"Percent",

						"width": 95,
					},
				]
			)

	columns.extend(
		[
			{
				"label":
					_("Total Plan"),

				"fieldname":
					"total_plan",

				"fieldtype":
					"Currency",

				"options":
					"Company:company:default_currency",

				"width": 140,
			},

			{
				"label":
					_("Total Actual"),

				"fieldname":
					"total_actual",

				"fieldtype":
					"Currency",

				"options":
					"Company:company:default_currency",

				"width": 140,
			},

			{
				"label":
					_("Total Variance"),

				"fieldname":
					"total_variance",

				"fieldtype":
					"Currency",

				"options":
					"Company:company:default_currency",

				"width": 140,
			},

			{
				"label":
					_("Total Util %"),

				"fieldname":
					"total_utilization",

				"fieldtype":
					"Percent",

				"width": 120,
			},
		]
	)

	return columns


# ============================================================
# ACCOUNT REPORT DATA
# ============================================================

def get_report_data_and_summary(
	filters,
	budget_accounts,
	branches,
	planned_map,
	actual_map
):

	account_names = frappe._dict(

		frappe.db.get_all(

			"Account",

			filters={
				"name": [
					"in",
					list(budget_accounts)
				]
			},

			fields=[
				"name",
				"account_name"
			],

			as_list=True,
		)
	)

	data = []

	group_by_branch = filters.get(
		"group_by_branch"
	)

	grand_plan = 0.0
	grand_actual = 0.0

	for acc in sorted(budget_accounts):

		account_has_plan = any(

			key[0] == acc
			and flt(value)

			for key, value
			in planned_map.items()
		)

		row = {

			"account":
				acc,

			"account_name":
				account_names.get(
					acc,
					""
				),

			"is_unplanned":
				0
				if account_has_plan
				else 1,
		}

		total_acc_plan = 0.0
		total_acc_actual = 0.0

		# ====================================================
		# GROUP BY BRANCH
		# ====================================================

		if (
			group_by_branch
			and branches
		):

			for branch in branches:

				branch_key = frappe.scrub(
					branch
				)

				plan = flt(
					planned_map.get(
						(
							acc,
							branch
						),
						0.0
					),
					2
				)

				actual = flt(
					actual_map.get(
						(
							acc,
							branch
						),
						0.0
					),
					2
				)

				variance = flt(
					plan - actual,
					2
				)

				if plan:

					util = (
						actual
						/ plan
						* 100.0
					)

				elif actual:

					util = 100.0

				else:

					util = 0.0

				row[
					f"{branch_key}_plan"
				] = plan

				row[
					f"{branch_key}_actual"
				] = actual

				row[
					f"{branch_key}_variance"
				] = variance

				row[
					f"{branch_key}_utilization"
				] = flt(
					util,
					2
				)

				total_acc_plan += plan
				total_acc_actual += actual

		# ====================================================
		# WITHOUT BRANCH GROUPING
		# ====================================================

		else:

			total_acc_plan = sum(

				flt(value)

				for key, value
				in planned_map.items()

				if key[0] == acc
			)

			total_acc_actual = sum(

				flt(value)

				for key, value
				in actual_map.items()

				if key[0] == acc
			)

		# ====================================================
		# TOTALS
		# ====================================================

		total_variance = flt(
			total_acc_plan
			- total_acc_actual,
			2
		)

		if total_acc_plan:

			total_util = (
				total_acc_actual
				/ total_acc_plan
				* 100.0
			)

		elif total_acc_actual:

			total_util = 100.0

		else:

			total_util = 0.0

		row["total_plan"] = flt(
			total_acc_plan,
			2
		)

		row["total_actual"] = flt(
			total_acc_actual,
			2
		)

		row["total_variance"] = (
			total_variance
		)

		row["total_utilization"] = flt(
			total_util,
			2
		)

		# ====================================================
		# ROW-LEVEL BUDGET FILTERS
		# (Only Over Budget / Only Without Plan)
		# ====================================================

		if not row_matches_budget_filters(
			filters,
			total_acc_plan,
			total_acc_actual,
			row["is_unplanned"]
		):

			continue

		grand_plan += (
			total_acc_plan
		)

		grand_actual += (
			total_acc_actual
		)

		data.append(row)

	# ========================================================
	# GRAND TOTAL
	# ========================================================

	if data:

		total_row = {

			"account":
				"",

			"account_name":
				_("Grand Total"),

			"is_total_row":
				1,
		}

		if (
			group_by_branch
			and branches
		):

			for branch in branches:

				branch_key = frappe.scrub(
					branch
				)

				b_plan = sum(
					r.get(
						f"{branch_key}_plan",
						0
					)
					for r in data
				)

				b_actual = sum(
					r.get(
						f"{branch_key}_actual",
						0
					)
					for r in data
				)

				b_variance = flt(
					b_plan - b_actual,
					2
				)

				if b_plan:

					b_util = (
						b_actual
						/ b_plan
						* 100.0
					)

				elif b_actual:

					b_util = 100.0

				else:

					b_util = 0.0

				total_row[
					f"{branch_key}_plan"
				] = flt(
					b_plan,
					2
				)

				total_row[
					f"{branch_key}_actual"
				] = flt(
					b_actual,
					2
				)

				total_row[
					f"{branch_key}_variance"
				] = b_variance

				total_row[
					f"{branch_key}_utilization"
				] = flt(
					b_util,
					2
				)

		grand_variance = flt(
			grand_plan
			- grand_actual,
			2
		)

		grand_util = (
			grand_actual
			/ grand_plan
			* 100.0
		) if grand_plan else 0.0

		total_row["total_plan"] = flt(
			grand_plan,
			2
		)

		total_row["total_actual"] = flt(
			grand_actual,
			2
		)

		total_row["total_variance"] = (
			grand_variance
		)

		total_row[
			"total_utilization"
		] = flt(
			grand_util,
			2
		)

		data.append(
			total_row
		)

	summary = build_summary(
		grand_plan,
		grand_actual
	)

	return data, summary


# ============================================================
# CHART
# ============================================================

def get_chart(data):

	rows = [
		r
		for r in data
		if not r.get(
			"is_total_row"
		)
	]

	if not rows:
		return None

	rows = sorted(
		rows,
		key=lambda r:
			r.get(
				"total_actual",
				0
			),
		reverse=True
	)[:10]

	return {

		"data": {

			"labels": [
				r.get(
					"account_name"
				)
				or r.get(
					"account"
				)
				for r in rows
			],

			"datasets": [

				{
					"name":
						_("Plan"),

					"values": [
						r.get(
							"total_plan",
							0
						)
						for r in rows
					],
				},

				{
					"name":
						_("Actual"),

					"values": [
						r.get(
							"total_actual",
							0
						)
						for r in rows
					],
				},
			],
		},

		"type":
			"bar",

		"colors": [
			"#5e64ff",
			"#ff5858"
		],

		"barOptions": {
			"stacked": 0
		},
	}


# ============================================================
# PROJECT COLUMNS
# ============================================================

def get_project_columns():

	return [

		{
			"label":
				_("Project"),

			"fieldname":
				"project",

			"fieldtype":
				"Link",

			"options":
				"Project",

			"width":
				220,
		},

		{
			"label":
				_("Plan"),

			"fieldname":
				"total_plan",

			"fieldtype":
				"Currency",

			"options":
				"Company:company:default_currency",

			"width":
				150,
		},

		{
			"label":
				_("Actual"),

			"fieldname":
				"total_actual",

			"fieldtype":
				"Currency",

			"options":
				"Company:company:default_currency",

			"width":
				150,
		},

		{
			"label":
				_("Variance"),

			"fieldname":
				"total_variance",

			"fieldtype":
				"Currency",

			"options":
				"Company:company:default_currency",

			"width":
				150,
		},

		{
			"label":
				_("Util %"),

			"fieldname":
				"total_utilization",

			"fieldtype":
				"Percent",

			"width":
				120,
		},
	]


# ============================================================
# PROJECT SUMMARY
# ============================================================

def get_project_summary_data(
	planned_raw,
	actual_raw,
	filters
):

	planned_by_project = aggregate_single(
		planned_raw,
		index=2
	)

	actual_by_project = aggregate_single(
		actual_raw,
		index=2
	)

	projects = sorted(
		set(planned_by_project)
		|
		set(actual_by_project)
	)

	data = []

	grand_plan = 0.0
	grand_actual = 0.0

	for project in projects:

		plan = flt(
			planned_by_project.get(
				project,
				0.0
			),
			2
		)

		actual = flt(
			actual_by_project.get(
				project,
				0.0
			),
			2
		)

		variance = flt(
			plan - actual,
			2
		)

		if plan:

			util = (
				actual
				/ plan
				* 100.0
			)

		elif actual:

			util = 100.0

		else:

			util = 0.0

		is_unplanned = (
			1
			if (plan == 0 and actual != 0)
			else 0
		)

		if not row_matches_budget_filters(
			filters,
			plan,
			actual,
			is_unplanned
		):

			continue

		grand_plan += plan
		grand_actual += actual

		data.append(
			{
				"project":
					project,

				"total_plan":
					plan,

				"total_actual":
					actual,

				"total_variance":
					variance,

				"total_utilization":
					flt(
						util,
						2
					),

				"is_unplanned":
					is_unplanned,
			}
		)

	if data:

		grand_variance = flt(
			grand_plan
			- grand_actual,
			2
		)

		grand_util = (
			grand_actual
			/ grand_plan
			* 100.0
		) if grand_plan else 0.0

		data.append(
			{
				"project":
					_("Grand Total"),

				"total_plan":
					flt(
						grand_plan,
						2
					),

				"total_actual":
					flt(
						grand_actual,
						2
					),

				"total_variance":
					grand_variance,

				"total_utilization":
					flt(
						grand_util,
						2
					),

				"is_total_row":
					1,
			}
		)

	summary = build_summary(
		grand_plan,
		grand_actual
	)

	return data, summary


# ============================================================
# PROJECT CHART
# ============================================================

def get_project_chart(data):

	rows = [
		r
		for r in data
		if not r.get(
			"is_total_row"
		)
	]

	if not rows:
		return None

	rows = sorted(
		rows,
		key=lambda r:
			r.get(
				"total_actual",
				0
			),
		reverse=True
	)[:10]

	return {

		"data": {

			"labels": [
				r.get(
					"project"
				)
				for r in rows
			],

			"datasets": [

				{
					"name":
						_("Plan"),

					"values": [
						r.get(
							"total_plan",
							0
						)
						for r in rows
					],
				},

				{
					"name":
						_("Actual"),

					"values": [
						r.get(
							"total_actual",
							0
						)
						for r in rows
					],
				},
			],
		},

		"type":
			"bar",

		"colors": [
			"#5e64ff",
			"#ff5858"
		],

		"barOptions": {
			"stacked": 0
		},
	}


# ============================================================
# SUMMARY VIEW
# (Company Branch -> Cost Center, split Admin / Operational)
# ============================================================

def get_summary_report(filters):

	# Summary mode ignores the Account Category filter, since it
	# always needs BOTH Admin (6xxxx) and Operational (5xxxx)
	# amounts to build the side-by-side columns.

	summary_filters = frappe._dict(filters)

	summary_filters["account_prefix"] = None

	planned_raw, _planned_accounts = get_planned_budgets(
		summary_filters
	)

	actual_raw = get_actual_costs_from_gl(
		summary_filters
	)

	data, grand = build_branch_summary(
		planned_raw,
		actual_raw,
		filters
	)

	columns = get_summary_columns()

	chart = get_summary_chart(data)

	summary = build_summary_with_categories(
		grand
	)

	return (
		columns,
		data,
		None,
		chart,
		summary
	)


def build_branch_summary(
	planned_raw,
	actual_raw,
	filters
):

	"""
	Builds a Branch -> Cost Center tree where each row carries
	Admin (account starts with 6) and Operational (account starts
	with 5) plan/actual amounts side by side.
	"""

	branch_map = {}

	def collect(raw_map, is_plan):

		for key, value in raw_map.items():

			account = key[0]

			if not account:
				continue

			prefix = account[:1]

			if prefix not in (
				ADMIN_PREFIX,
				OPERATIONAL_PREFIX
			):

				continue

			branch = key[1] or "Unassigned"

			cost_center = (
				key[3]
				if len(key) > 3
				else None
			)

			cost_center = (
				cost_center
				or "No Cost Center"
			)

			cc_entry = branch_map.setdefault(
				branch,
				{}
			).setdefault(
				cost_center,
				{
					"admin_plan": 0.0,
					"admin_actual": 0.0,
					"operational_plan": 0.0,
					"operational_actual": 0.0,
				}
			)

			field = (
				"admin"
				if prefix == ADMIN_PREFIX
				else "operational"
			)

			field += (
				"_plan"
				if is_plan
				else "_actual"
			)

			cc_entry[field] += flt(value)

	collect(planned_raw, is_plan=True)
	collect(actual_raw, is_plan=False)

	data = []

	grand = {
		"admin_plan": 0.0,
		"admin_actual": 0.0,
		"operational_plan": 0.0,
		"operational_actual": 0.0,
	}

	for branch in sorted(branch_map.keys()):

		cost_centers = branch_map[branch]

		kept_children = []

		for cost_center in sorted(cost_centers.keys()):

			vals = cost_centers[cost_center]

			total_plan = flt(
				vals["admin_plan"]
				+ vals["operational_plan"],
				2
			)

			total_actual = flt(
				vals["admin_actual"]
				+ vals["operational_actual"],
				2
			)

			is_unplanned = (
				1
				if (
					total_plan == 0
					and total_actual != 0
				)
				else 0
			)

			if not row_matches_budget_filters(
				filters,
				total_plan,
				total_actual,
				is_unplanned
			):

				continue

			kept_children.append(
				(
					cost_center,
					vals,
					is_unplanned
				)
			)

		if not kept_children:
			continue

		branch_totals = {
			"admin_plan": 0.0,
			"admin_actual": 0.0,
			"operational_plan": 0.0,
			"operational_actual": 0.0,
		}

		for _cc, vals, _iu in kept_children:

			for k in branch_totals:

				branch_totals[k] += vals[k]

		branch_row = make_summary_row(
			branch,
			branch_totals,
			indent=0,
			is_group=1
		)

		data.append(branch_row)

		for k in grand:

			grand[k] += branch_totals[k]

		for cost_center, vals, is_unplanned in kept_children:

			child_row = make_summary_row(
				cost_center,
				vals,
				indent=1,
				is_group=0
			)

			child_row["is_unplanned"] = is_unplanned

			data.append(child_row)

	if data:

		total_row = make_summary_row(
			_("Grand Total"),
			grand,
			indent=0,
			is_group=0
		)

		total_row["is_total_row"] = 1

		data.append(total_row)

	return data, grand


def make_summary_row(label, vals, indent, is_group):

	admin_plan = flt(vals["admin_plan"], 2)
	admin_actual = flt(vals["admin_actual"], 2)

	operational_plan = flt(vals["operational_plan"], 2)
	operational_actual = flt(vals["operational_actual"], 2)

	admin_variance = flt(
		admin_plan - admin_actual,
		2
	)

	operational_variance = flt(
		operational_plan - operational_actual,
		2
	)

	if admin_plan:

		admin_util = (
			admin_actual
			/ admin_plan
			* 100.0
		)

	elif admin_actual:

		admin_util = 100.0

	else:

		admin_util = 0.0

	if operational_plan:

		operational_util = (
			operational_actual
			/ operational_plan
			* 100.0
		)

	elif operational_actual:

		operational_util = 100.0

	else:

		operational_util = 0.0

	total_plan = flt(
		admin_plan + operational_plan,
		2
	)

	total_actual = flt(
		admin_actual + operational_actual,
		2
	)

	total_variance = flt(
		total_plan - total_actual,
		2
	)

	if total_plan:

		total_util = (
			total_actual
			/ total_plan
			* 100.0
		)

	elif total_actual:

		total_util = 100.0

	else:

		total_util = 0.0

	return {

		"label": label,
		"indent": indent,
		"is_group": is_group,

		"admin_plan": admin_plan,
		"admin_actual": admin_actual,
		"admin_variance": admin_variance,
		"admin_utilization": flt(admin_util, 2),

		"operational_plan": operational_plan,
		"operational_actual": operational_actual,
		"operational_variance": operational_variance,
		"operational_utilization": flt(operational_util, 2),

		"total_plan": total_plan,
		"total_actual": total_actual,
		"total_variance": total_variance,
		"total_utilization": flt(total_util, 2),
	}


def get_summary_columns():

	return [

		{
			"label": _("Branch / Cost Center"),
			"fieldname": "label",
			"fieldtype": "Data",
			"width": 240,
		},

		{
			"label": _("Admin Plan"),
			"fieldname": "admin_plan",
			"fieldtype": "Currency",
			"options": "Company:company:default_currency",
			"width": 120,
		},

		{
			"label": _("Admin Actual"),
			"fieldname": "admin_actual",
			"fieldtype": "Currency",
			"options": "Company:company:default_currency",
			"width": 120,
		},

		{
			"label": _("Admin Variance"),
			"fieldname": "admin_variance",
			"fieldtype": "Currency",
			"options": "Company:company:default_currency",
			"width": 120,
		},

		{
			"label": _("Admin Util %"),
			"fieldname": "admin_utilization",
			"fieldtype": "Percent",
			"width": 95,
		},

		{
			"label": _("Operational Plan"),
			"fieldname": "operational_plan",
			"fieldtype": "Currency",
			"options": "Company:company:default_currency",
			"width": 130,
		},

		{
			"label": _("Operational Actual"),
			"fieldname": "operational_actual",
			"fieldtype": "Currency",
			"options": "Company:company:default_currency",
			"width": 130,
		},

		{
			"label": _("Operational Variance"),
			"fieldname": "operational_variance",
			"fieldtype": "Currency",
			"options": "Company:company:default_currency",
			"width": 130,
		},

		{
			"label": _("Operational Util %"),
			"fieldname": "operational_utilization",
			"fieldtype": "Percent",
			"width": 100,
		},

		{
			"label": _("Total Plan"),
			"fieldname": "total_plan",
			"fieldtype": "Currency",
			"options": "Company:company:default_currency",
			"width": 130,
		},

		{
			"label": _("Total Actual"),
			"fieldname": "total_actual",
			"fieldtype": "Currency",
			"options": "Company:company:default_currency",
			"width": 130,
		},

		{
			"label": _("Total Variance"),
			"fieldname": "total_variance",
			"fieldtype": "Currency",
			"options": "Company:company:default_currency",
			"width": 130,
		},

		{
			"label": _("Total Util %"),
			"fieldname": "total_utilization",
			"fieldtype": "Percent",
			"width": 110,
		},
	]


def get_summary_chart(data):

	rows = [
		r
		for r in data
		if r.get("is_group")
		and not r.get("is_total_row")
	]

	if not rows:
		return None

	rows = sorted(
		rows,
		key=lambda r: r.get("total_actual", 0),
		reverse=True
	)[:10]

	return {

		"data": {

			"labels": [
				r.get("label")
				for r in rows
			],

			"datasets": [

				{
					"name": _("Admin Actual"),

					"values": [
						r.get("admin_actual", 0)
						for r in rows
					],
				},

				{
					"name": _("Operational Actual"),

					"values": [
						r.get("operational_actual", 0)
						for r in rows
					],
				},
			],
		},

		"type": "bar",

		"colors": [
			"#f59f00",
			"#5e64ff"
		],

		"barOptions": {
			"stacked": 1
		},
	}


def build_summary_with_categories(grand):

	admin_plan = grand.get("admin_plan", 0.0)
	admin_actual = grand.get("admin_actual", 0.0)

	operational_plan = grand.get("operational_plan", 0.0)
	operational_actual = grand.get("operational_actual", 0.0)

	total_plan = admin_plan + operational_plan
	total_actual = admin_actual + operational_actual

	total_variance = total_plan - total_actual

	overall_utilization = (
		total_actual
		/ total_plan
		* 100.0
	) if total_plan else 0.0

	return [

		{
			"value": admin_plan,
			"label": _("Total Admin Plan"),
			"datatype": "Currency",
		},

		{
			"value": admin_actual,
			"label": _("Total Admin Actual"),
			"datatype": "Currency",
		},

		{
			"value": operational_plan,
			"label": _("Total Operational Plan"),
			"datatype": "Currency",
		},

		{
			"value": operational_actual,
			"label": _("Total Operational Actual"),
			"datatype": "Currency",
		},

		{
			"value": total_variance,
			"label": _("Total Variance"),
			"datatype": "Currency",
			"indicator":
				"Green"
				if total_variance >= 0
				else "Red",
		},

		{
			"value": overall_utilization,
			"label": _("Overall Utilization"),
			"datatype": "Percent",
			"indicator":
				"Green"
				if (
					total_plan
					and overall_utilization <= 100
				)
				else "Red",
		},
	]


# ============================================================
# SUMMARY (Account / Branch / Project mode cards)
# ============================================================

def build_summary(
	grand_plan,
	grand_actual
):

	grand_variance = (
		grand_plan
		- grand_actual
	)

	overall_utilization = (
		grand_actual
		/ grand_plan
		* 100.0
	) if grand_plan else 0.0

	return [

		{
			"value":
				grand_plan,

			"label":
				_("Total Budget Plan"),

			"datatype":
				"Currency",
		},

		{
			"value":
				grand_actual,

			"label":
				_("Total Actual Expense"),

			"datatype":
				"Currency",
		},

		{
			"value":
				grand_variance,

			"label":
				_("Total Variance"),

			"datatype":
				"Currency",

			"indicator":
				"Green"
				if grand_variance >= 0
				else "Red",
		},

		{
			"value":
				overall_utilization,

			"label":
				_("Overall Utilization"),

			"datatype":
				"Percent",

			"indicator":
				"Green"
				if (
					grand_plan
					and overall_utilization <= 100
				)
				else "Red",
		},
	]


# ============================================================
# AGGREGATE ACCOUNT + BRANCH
# ============================================================

def aggregate_account_branch(raw_map):

	agg = {}

	for key, value in raw_map.items():

		account = key[0]
		branch = key[1]

		agg_key = (
			account,
			branch
		)

		agg[agg_key] = (
			agg.get(
				agg_key,
				0.0
			)
			+ value
		)

	return agg


# ============================================================
# AGGREGATE SINGLE
# ============================================================

def aggregate_single(
	raw_map,
	index
):

	agg = {}

	for key, value in raw_map.items():

		agg_key = key[index]

		agg[agg_key] = (
			agg.get(
				agg_key,
				0.0
			)
			+ value
		)

	return agg


# ============================================================
# DISTINCT VALUES
# ============================================================

def get_distinct_values(
	planned_raw,
	actual_raw,
	index
):

	values = {
		key[index]
		for key in planned_raw
	}

	values.update(
		key[index]
		for key in actual_raw
	)

	return sorted(values)


# ============================================================
# GET PLANNED BUDGETS
#
# Raw map keys are now 4-tuples:
#   (account, branch, project, cost_center)
#
# Existing consumers (aggregate_account_branch, aggregate_single,
# get_distinct_values) only look at fixed index positions, so this
# stays fully backward compatible while making cost_center
# available to the new Summary view.
# ============================================================

def get_planned_budgets(filters):

	conditions = [
		"b.docstatus = 1"
	]

	values = {}

	# --------------------------------------------------------
	# Company
	# --------------------------------------------------------

	if filters.get("company"):

		conditions.append(
			"b.company = %(company)s"
		)

		values["company"] = (
			filters.get("company")
		)

	# --------------------------------------------------------
	# Fiscal Year
	# --------------------------------------------------------

	if filters.get("fiscal_year"):

		conditions.append(
			"b.fiscal_year = %(fiscal_year)s"
		)

		values["fiscal_year"] = (
			filters.get("fiscal_year")
		)

	# --------------------------------------------------------
	# Company Branch
	# --------------------------------------------------------

	if filters.get(
		"company_branch_list"
	):

		conditions.append(
			"""
			b.company_branch IN %(company_branch_list)s
			"""
		)

		values[
			"company_branch_list"
		] = tuple(
			filters[
				"company_branch_list"
			]
		)

	# --------------------------------------------------------
	# Project
	# --------------------------------------------------------

	if filters.get(
		"project_list"
	):

		conditions.append(
			"""
			b.project IN %(project_list)s
			"""
		)

		values[
			"project_list"
		] = tuple(
			filters[
				"project_list"
			]
		)

	# --------------------------------------------------------
	# Cost Center
	# --------------------------------------------------------

	if filters.get(
		"cost_center_list"
	):

		conditions.append(
			"""
			b.cost_center IN %(cost_center_list)s
			"""
		)

		values[
			"cost_center_list"
		] = tuple(
			filters[
				"cost_center_list"
			]
		)

	# --------------------------------------------------------
	# Account Category
	#
	# Operational = 5xxxx
	# Admin       = 6xxxx
	# --------------------------------------------------------

	if filters.get(
		"account_prefix"
	):

		conditions.append(
			"""
			ba.account LIKE %(account_prefix_like)s
			"""
		)

		values[
			"account_prefix_like"
		] = (
			f"{filters['account_prefix']}%"
		)

	where_clause = " AND ".join(
		conditions
	)

	# ========================================================
	# BUDGET QUERY
	# ========================================================

	raw_budgets = frappe.db.sql(

		f"""
		SELECT

			ba.account,

			b.company_branch,

			b.project,

			b.cost_center,

			ba.budget_amount,

			b.wwc_monthly_distribution,

			dist.budget_month,

			dist.start_date,

			dist.end_date,

			dist.percent

		FROM `tabWWC Budget` b

		INNER JOIN
			`tabWWC Budget Account` ba
			ON ba.parent = b.name

		LEFT JOIN
			`tabWWC Budget Distribution` dist
			ON dist.parent =
				b.wwc_monthly_distribution

		WHERE {where_clause}
		""",

		values,

		as_dict=True,
	)

	planned_map = {}

	budget_accounts = set()

	from_date = (
		getdate(
			filters.get("from_date")
		)
		if filters.get("from_date")
		else None
	)

	to_date = (
		getdate(
			filters.get("to_date")
		)
		if filters.get("to_date")
		else None
	)

	target_months = (
		filters.get(
			"budget_month_list"
		)
		or []
	)

	# ========================================================
	# PROCESS BUDGET
	# ========================================================

	for row in raw_budgets:

		account = row.account

		branch = (
			row.company_branch
			or "Unassigned"
		)

		project = (
			row.project
			or "No Project"
		)

		cost_center = (
			row.cost_center
			or "No Cost Center"
		)

		total_amount = flt(
			row.budget_amount
		)

		budget_accounts.add(
			account
		)

		key = (
			account,
			branch,
			project,
			cost_center
		)

		planned_map.setdefault(
			key,
			0.0
		)

		# ----------------------------------------------------
		# No monthly distribution
		# ----------------------------------------------------

		if not row.wwc_monthly_distribution:

			planned_map[key] += (
				total_amount
			)

			continue

		# ----------------------------------------------------
		# Budget Month
		# ----------------------------------------------------

		if (
			target_months
			and row.budget_month
			not in target_months
		):

			continue

		dist_start = (
			getdate(
				row.start_date
			)
			if row.start_date
			else None
		)

		dist_end = (
			getdate(
				row.end_date
			)
			if row.end_date
			else None
		)

		dist_percent = flt(
			row.percent
		)

		ratio = calculate_overlap_ratio(
			dist_start,
			dist_end,
			from_date,
			to_date
		)

		planned_map[key] += (
			total_amount
			* (
				dist_percent
				/ 100.0
			)
			* ratio
		)

	return (
		planned_map,
		sorted(
			budget_accounts
		)
	)


# ============================================================
# DATE OVERLAP
# ============================================================

def calculate_overlap_ratio(
	dist_start,
	dist_end,
	filter_from,
	filter_to
):

	if (
		not dist_start
		or not dist_end
	):

		return 1.0

	overlap_start = (
		max(
			dist_start,
			filter_from
		)
		if filter_from
		else dist_start
	)

	overlap_end = (
		min(
			dist_end,
			filter_to
		)
		if filter_to
		else dist_end
	)

	if overlap_start > overlap_end:

		return 0.0

	total_dist_days = (
		date_diff(
			dist_end,
			dist_start
		)
		+ 1
	)

	overlapping_days = (
		date_diff(
			overlap_end,
			overlap_start
		)
		+ 1
	)

	if total_dist_days <= 0:

		return 0.0

	return (
		flt(
			overlapping_days
		)
		/
		flt(
			total_dist_days
		)
	)


# ============================================================
# GET ACTUAL EXPENSES FROM GL
#
# Raw map keys are now 4-tuples:
#   (account, branch, project, cost_center)
# ============================================================

def get_actual_costs_from_gl(filters):

	conditions = [

		# Only non-cancelled GL
		"gle.is_cancelled = 0",

		# Only Expense root type
		"acc.root_type = 'Expense'",

		# Only leaf accounts
		"acc.is_group = 0",
	]

	values = {}

	# --------------------------------------------------------
	# Account Category
	#
	# Operational Expense = 5xxxx
	# Admin Expense       = 6xxxx
	# --------------------------------------------------------

	if filters.get(
		"account_prefix"
	):

		conditions.append(
			"""
			gle.account LIKE %(account_prefix_like)s
			"""
		)

		values[
			"account_prefix_like"
		] = (
			f"{filters['account_prefix']}%"
		)

	# --------------------------------------------------------
	# Company
	# --------------------------------------------------------

	if filters.get("company"):

		conditions.append(
			"gle.company = %(company)s"
		)

		values["company"] = (
			filters.get(
				"company"
			)
		)

	# --------------------------------------------------------
	# Company Branch
	# --------------------------------------------------------

	if filters.get(
		"company_branch_list"
	):

		conditions.append(
			"""
			COALESCE(
				gle.branch,
				gle.company_branch
			) IN %(company_branch_list)s
			"""
		)

		values[
			"company_branch_list"
		] = tuple(
			filters[
				"company_branch_list"
			]
		)

	# --------------------------------------------------------
	# Cost Center
	# --------------------------------------------------------

	if filters.get(
		"cost_center_list"
	):

		conditions.append(
			"""
			gle.cost_center IN %(cost_center_list)s
			"""
		)

		values[
			"cost_center_list"
		] = tuple(
			filters[
				"cost_center_list"
			]
		)

	# --------------------------------------------------------
	# Project
	# --------------------------------------------------------

	if filters.get(
		"project_list"
	):

		conditions.append(
			"""
			gle.project IN %(project_list)s
			"""
		)

		values[
			"project_list"
		] = tuple(
			filters[
				"project_list"
			]
		)

	# --------------------------------------------------------
	# From Date
	# --------------------------------------------------------

	if filters.get(
		"from_date"
	):

		conditions.append(
			"""
			gle.posting_date >= %(from_date)s
			"""
		)

		values[
			"from_date"
		] = filters.get(
			"from_date"
		)

	# --------------------------------------------------------
	# To Date
	# --------------------------------------------------------

	if filters.get(
		"to_date"
	):

		conditions.append(
			"""
			gle.posting_date <= %(to_date)s
			"""
		)

		values[
			"to_date"
		] = filters.get(
			"to_date"
		)

	where_clause = " AND ".join(
		conditions
	)

	# ========================================================
	# GL QUERY
	# ========================================================

	gl_data = frappe.db.sql(

		f"""
		SELECT

			gle.account,

			COALESCE(
				gle.branch,
				gle.company_branch,
				'Unassigned'
			) AS branch,

			COALESCE(
				gle.project,
				'No Project'
			) AS project,

			COALESCE(
				gle.cost_center,
				'No Cost Center'
			) AS cost_center,

			SUM(
				gle.debit
				- gle.credit
			) AS actual_cost

		FROM `tabGL Entry` gle

		INNER JOIN
			`tabAccount` acc
			ON acc.name = gle.account

		WHERE {where_clause}

		GROUP BY

			gle.account,

			COALESCE(
				gle.branch,
				gle.company_branch,
				'Unassigned'
			),

			COALESCE(
				gle.project,
				'No Project'
			),

			COALESCE(
				gle.cost_center,
				'No Cost Center'
			)
		""",

		values,

		as_dict=True,
	)

	return {

		(
			row.account,
			row.branch,
			row.project,
			row.cost_center
		):
			flt(
				row.actual_cost
			)

		for row in gl_data
	}


# ============================================================
# END
# ============================================================
