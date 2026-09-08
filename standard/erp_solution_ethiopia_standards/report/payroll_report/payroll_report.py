# Copyright (c) 2026, Muhammed Nurhusien
# For license information, please see license.txt
#
# One Script Report covering all 6 payroll report views. The "Report Type"
# filter picks which columns/data function runs; every view shares the same
# Company Branch / Budget Year / Budget Month / Document filters (used to
# scope the data, but not repeated as display columns since they're already
# visible in the filter bar).
#
# Install path (adjust the app/module name to match your bench app):
#   apps/standard/standard/erp_solution_ethiopia_standards/report/payroll_report/

import frappe
from frappe import _
from frappe.utils import flt


def sum_field(data, fieldname):
    """Sum a numeric field across a list of result dicts, safely."""
    return sum(flt(row.get(fieldname)) for row in data)


# ---------------------------------------------------------------------------
# Shared filter -> WHERE clause helper
# ---------------------------------------------------------------------------

def get_conditions(filters, parent_alias="p"):
    """Build a WHERE-clause fragment + params dict from the standard
    filter set, scoped against the Employee Payroll parent table.
    company_branch / budget_year / budget_month are Link fields, so their
    values are simply the linked doctype's `name`."""

    filters = filters or {}
    conditions = []
    values = {}

    if filters.get("company_branch"):
        conditions.append(f"{parent_alias}.company_branch = %(company_branch)s")
        values["company_branch"] = filters.get("company_branch")

    if filters.get("budget_year"):
        conditions.append(f"{parent_alias}.budget_year = %(budget_year)s")
        values["budget_year"] = filters.get("budget_year")

    if filters.get("budget_month"):
        conditions.append(f"{parent_alias}.budget_month = %(budget_month)s")
        values["budget_month"] = filters.get("budget_month")

    if filters.get("document_name"):
        conditions.append(f"{parent_alias}.name = %(document_name)s")
        values["document_name"] = filters.get("document_name")

    where_clause = ""
    if conditions:
        where_clause = " AND " + " AND ".join(conditions)

    return where_clause, values


# ---------------------------------------------------------------------------
# Deduction type -> fieldname map (used by the Deduction view's
# "Deduction Type" filter)
# ---------------------------------------------------------------------------

DEDUCTION_TYPE_MAP = {
    "Pension (7%)": "pension_7",
    "Income Tax": "income_tax",
    "Credit Association (AWWCE)": "credit_association_awwce",
    "ADA": "ada",
    "EDIR": "edir",
    "AIDS Fund": "aids_fund",
    "ANDM": "andm",
    "Cost Sharing": "cost_sharing",
    "Red Cross": "red_cross",
    "Operator Association": "operator_association",
    "Abay Dam": "abay_dam",
    "Credit Association (Drilling)": "credit_association_drilling",
    "Shemachoche": "shemachoche",
    "Defense Contribution": "defense_contribution",
    "Other 1": "other_one",
    "Other 2": "other_two",
    "Other 3": "other_three",
    "Penalty Deduction": "penalty_deduction",
    "Advance Deduction": "advance_deduction",
    "Other Variable Deduction 1": "other_variable_deduction_one",
    "Other Variable Deduction 2": "other_variable_deduction_two",
    "Recurring Deduction 1": "recurring_deduction_one",
    "Recurring Deduction 2": "recurring_deduction_two",
}


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def execute(filters=None):
    filters = filters or {}
    report_type = filters.get("report_type") or "Payroll Sheet"

    if report_type == "Payroll Sheet":
        columns = payroll_sheet_columns()
        data = payroll_sheet_data(filters)
        return columns, data, None, None, payroll_sheet_summary(data)

    if report_type == "Bank Payment":
        columns = bank_payment_columns()
        data = bank_payment_data(filters)
        return columns, data, None, None, bank_payment_summary(data)

    if report_type == "Deduction":
        columns, data = deduction_report(filters)
        return columns, data, None, None, deduction_summary(data, filters.get("deduction_type"))

    if report_type == "Pay Slip":
        result = pay_slip_report(filters)
        if len(result) == 5:
            # Single-employee pivot already carries its own summary cards
            return result
        columns, data = result
        return columns, data, None, None, pay_slip_summary(data)

    if report_type == "Pay Summary":
        columns = pay_summary_columns()
        data = pay_summary_data(filters)
        return columns, data, None, None, pay_summary_summary(data)

    if report_type == "Data Summary":
        columns = data_summary_columns()
        data = data_summary_data(filters)
        return columns, data, None, None, data_summary_summary(data)

    frappe.throw(_("Unknown Report Type: {0}").format(report_type))


# ---------------------------------------------------------------------------
# 1. Payroll Sheet
# ---------------------------------------------------------------------------

def payroll_sheet_columns():
    return [
        {"label": _("Employee ID"), "fieldname": "employee_id", "fieldtype": "Link",
         "options": "Employee", "width": 110},
        {"label": _("Employee Name"), "fieldname": "employee_name", "fieldtype": "Data", "width": 160},
        {"label": _("Department"), "fieldname": "department", "fieldtype": "Link",
         "options": "Department", "width": 130},
        {"label": _("Designation"), "fieldname": "designation", "fieldtype": "Link",
         "options": "Designation", "width": 120},
        {"label": _("Basic Salary"), "fieldname": "basic_salary", "fieldtype": "Currency", "width": 110},
        {"label": _("Working Days"), "fieldname": "working_days", "fieldtype": "Float", "width": 100},
        {"label": _("Taxable Allowance"), "fieldname": "total_taxable_allowance",
         "fieldtype": "Currency", "width": 130},
        {"label": _("Non-Taxable Allowance"), "fieldname": "total_non_taxable_amount",
         "fieldtype": "Currency", "width": 150},
        {"label": _("Total Earning"), "fieldname": "total_earning", "fieldtype": "Currency", "width": 120},
        {"label": _("Pension 7%"), "fieldname": "pension_7", "fieldtype": "Currency", "width": 100},
        {"label": _("Pension 11%"), "fieldname": "pension_11", "fieldtype": "Currency", "width": 100},
        {"label": _("Income Tax"), "fieldname": "income_tax", "fieldtype": "Currency", "width": 100},
        {"label": _("Other Deduction"), "fieldname": "other_deduction", "fieldtype": "Currency", "width": 130},
        {"label": _("Total Deduction"), "fieldname": "total_deduction", "fieldtype": "Currency", "width": 130},
        {"label": _("Net Payment"), "fieldname": "net_payment", "fieldtype": "Currency", "width": 130},
    ]


def payroll_sheet_data(filters):
    conditions, values = get_conditions(filters, parent_alias="p")
    return frappe.db.sql(
        f"""
        SELECT
            c.employee_id, c.employee_name,
            c.department, c.designation,
            c.basic_salary, c.working_days,
            c.total_taxable_allowance, c.total_non_taxable_amount, c.total_earning,
            c.pension_7, c.pension_11, c.income_tax,
            c.total_deduction, 
            (COALESCE(c.total_deduction, 0) - COALESCE(c.pension_7, 0) - COALESCE(c.income_tax, 0)) AS other_deduction,
            c.net_payment
        FROM `tabEmployee Payroll Sheet` c
        INNER JOIN `tabEmployee Payroll` p ON p.name = c.parent
        WHERE c.parenttype = 'Employee Payroll' {conditions}
        ORDER BY c.employee_name
        """,
        values,
        as_dict=True,
    )


def payroll_sheet_summary(data):
    return [
        {"value": len(data), "label": _("Employees"), "datatype": "Int"},
        {"value": sum_field(data, "basic_salary"), "label": _("Total Basic Salary"), "datatype": "Currency"},
        {"value": sum_field(data, "total_earning"), "label": _("Total Earning"), "datatype": "Currency"},
        {"value": sum_field(data, "total_deduction"), "label": _("Total Deduction"), "datatype": "Currency"},
        {"value": sum_field(data, "net_payment"), "label": _("Total Net Payment"),
         "datatype": "Currency", "indicator": "Green"},
    ]


# ---------------------------------------------------------------------------
# 2. Bank Payment
# ---------------------------------------------------------------------------

def bank_payment_columns():
    return [
        {"label": _("Employee ID"), "fieldname": "employee_id", "fieldtype": "Link",
         "options": "Employee", "width": 110},
        {"label": _("Employee Name"), "fieldname": "employee_name", "fieldtype": "Data", "width": 200},
        {"label": _("Bank Account No"), "fieldname": "bank_ac_no", "fieldtype": "Data", "width": 170},
        {"label": _("Net Payment"), "fieldname": "net_payment", "fieldtype": "Currency", "width": 150},
    ]


def bank_payment_data(filters):
    conditions, values = get_conditions(filters, parent_alias="p")
    return frappe.db.sql(
        f"""
        SELECT
            c.employee_id, c.employee_name,
            c.bank_ac_no, c.net_payment
        FROM `tabEmployee Payroll Sheet` c
        INNER JOIN `tabEmployee Payroll` p ON p.name = c.parent
        WHERE c.parenttype = 'Employee Payroll'
          AND c.bank_ac_no IS NOT NULL AND c.bank_ac_no != ''
          {conditions}
        ORDER BY c.employee_name
        """,
        values,
        as_dict=True,
    )


def bank_payment_summary(data):
    return [
        {"value": len(data), "label": _("Employees (with bank account)"), "datatype": "Int"},
        {"value": sum_field(data, "net_payment"), "label": _("Total Bank Transfer"),
         "datatype": "Currency", "indicator": "Green"},
    ]


# ---------------------------------------------------------------------------
# 3. Deduction
# ---------------------------------------------------------------------------

def deduction_report(filters):
    """If a specific Deduction Type is picked, narrow to just the employees
    who actually have a non-zero amount for that one deduction (a focused
    'who is being deducted for X' view). Otherwise show the full breakdown
    of every deduction field, as before."""

    deduction_type = filters.get("deduction_type")

    if deduction_type and deduction_type in DEDUCTION_TYPE_MAP:
        return deduction_single_type_columns(deduction_type), deduction_single_type_data(
            filters, DEDUCTION_TYPE_MAP[deduction_type], deduction_type
        )

    return deduction_columns(), deduction_data(filters)


def deduction_single_type_columns(deduction_type_label):
    return [
        {"label": _("Employee ID"), "fieldname": "employee_id", "fieldtype": "Link",
         "options": "Employee", "width": 110},
        {"label": _("Employee Name"), "fieldname": "employee_name", "fieldtype": "Data", "width": 180},
        {"label": _("Department"), "fieldname": "department", "fieldtype": "Link",
         "options": "Department", "width": 140},
        {"label": _(deduction_type_label), "fieldname": "deduction_amount",
         "fieldtype": "Currency", "width": 150},
        {"label": _("Total Deduction"), "fieldname": "total_deduction", "fieldtype": "Currency", "width": 140},
    ]


def deduction_single_type_data(filters, fieldname, label):
    conditions, values = get_conditions(filters, parent_alias="p")
    return frappe.db.sql(
        f"""
        SELECT
            c.employee_id, c.employee_name, c.department,
            c.{fieldname} AS deduction_amount,
            c.total_deduction
        FROM `tabEmployee Payroll Sheet` c
        INNER JOIN `tabEmployee Payroll` p ON p.name = c.parent
        WHERE c.parenttype = 'Employee Payroll'
          AND c.{fieldname} > 0
          {conditions}
        ORDER BY c.{fieldname} DESC
        """,
        values,
        as_dict=True,
    )


def deduction_columns():
    return [
        {"label": _("Employee ID"), "fieldname": "employee_id", "fieldtype": "Link",
         "options": "Employee", "width": 110},
        {"label": _("Employee Name"), "fieldname": "employee_name", "fieldtype": "Data", "width": 160},
        {"label": _("Pension 7%"), "fieldname": "pension_7", "fieldtype": "Currency", "width": 100},
        {"label": _("Income Tax"), "fieldname": "income_tax", "fieldtype": "Currency", "width": 100},
        {"label": _("Credit Assoc.(AWWCE)"), "fieldname": "credit_association_awwce", "fieldtype": "Currency", "width": 130},
        {"label": _("ADA"), "fieldname": "ada", "fieldtype": "Currency", "width": 90},
        {"label": _("EDIR"), "fieldname": "edir", "fieldtype": "Currency", "width": 90},
        {"label": _("AIDS Fund"), "fieldname": "aids_fund", "fieldtype": "Currency", "width": 100},
        {"label": _("ANDM"), "fieldname": "andm", "fieldtype": "Currency", "width": 90},
        {"label": _("Cost Sharing"), "fieldname": "cost_sharing", "fieldtype": "Currency", "width": 110},
        {"label": _("Red Cross"), "fieldname": "red_cross", "fieldtype": "Currency", "width": 100},
        {"label": _("Operator Assoc."), "fieldname": "operator_association", "fieldtype": "Currency", "width": 120},
        {"label": _("Abay Dam"), "fieldname": "abay_dam", "fieldtype": "Currency", "width": 100},
        {"label": _("Credit Assoc.(Drilling)"), "fieldname": "credit_association_drilling", "fieldtype": "Currency", "width": 140},
        {"label": _("Shemachoche"), "fieldname": "shemachoche", "fieldtype": "Currency", "width": 110},
        {"label": _("Defense Contribution"), "fieldname": "defense_contribution", "fieldtype": "Currency", "width": 140},
        {"label": _("Other 1"), "fieldname": "other_one", "fieldtype": "Currency", "width": 90},
        {"label": _("Other 2"), "fieldname": "other_two", "fieldtype": "Currency", "width": 90},
        {"label": _("Other 3"), "fieldname": "other_three", "fieldtype": "Currency", "width": 90},
        {"label": _("Penalty Deduction"), "fieldname": "penalty_deduction", "fieldtype": "Currency", "width": 130},
        {"label": _("Advance Deduction"), "fieldname": "advance_deduction", "fieldtype": "Currency", "width": 130},
        {"label": _("Other Var. Ded. 1"), "fieldname": "other_variable_deduction_one", "fieldtype": "Currency", "width": 130},
        {"label": _("Other Var. Ded. 2"), "fieldname": "other_variable_deduction_two", "fieldtype": "Currency", "width": 130},
        {"label": _("Recurring Ded. 1"), "fieldname": "recurring_deduction_one", "fieldtype": "Currency", "width": 120},
        {"label": _("Recurring Ded. 2"), "fieldname": "recurring_deduction_two", "fieldtype": "Currency", "width": 120},
        {"label": _("Total Deduction"), "fieldname": "total_deduction", "fieldtype": "Currency", "width": 130},
    ]


def deduction_data(filters):
    conditions, values = get_conditions(filters, parent_alias="p")
    return frappe.db.sql(
        f"""
        SELECT
            c.employee_id, c.employee_name,
            c.pension_7, c.income_tax,
            c.credit_association_awwce, c.ada, c.edir, c.aids_fund, c.andm,
            c.cost_sharing, c.red_cross, c.operator_association, c.abay_dam,
            c.credit_association_drilling, c.shemachoche, c.defense_contribution,
            c.other_one, c.other_two, c.other_three,
            c.penalty_deduction, c.advance_deduction,
            c.other_variable_deduction_one, c.other_variable_deduction_two,
            c.recurring_deduction_one, c.recurring_deduction_two,
            c.total_deduction
        FROM `tabEmployee Payroll Sheet` c
        INNER JOIN `tabEmployee Payroll` p ON p.name = c.parent
        WHERE c.parenttype = 'Employee Payroll' {conditions}
        ORDER BY c.employee_name
        """,
        values,
        as_dict=True,
    )


def deduction_summary(data, deduction_type):
    if deduction_type:
        return [
            {"value": len(data), "label": _("Employees Affected"), "datatype": "Int"},
            {"value": sum_field(data, "deduction_amount"), "label": _("{0} Total").format(deduction_type),
             "datatype": "Currency", "indicator": "Red"},
            {"value": sum_field(data, "total_deduction"), "label": _("Combined Total Deduction"),
             "datatype": "Currency"},
        ]

    return [
        {"value": len(data), "label": _("Employees"), "datatype": "Int"},
        {"value": sum_field(data, "income_tax"), "label": _("Total Income Tax"), "datatype": "Currency"},
        {"value": sum_field(data, "pension_7"), "label": _("Total Pension (7%)"), "datatype": "Currency"},
        {"value": sum_field(data, "total_deduction"), "label": _("Total Deduction"),
         "datatype": "Currency", "indicator": "Red"},
    ]


# ---------------------------------------------------------------------------
# 4. Pay Slip
# ---------------------------------------------------------------------------

EARNING_FIELDS = [
    ("Basic Salary", "basic_salary"),
    ("Prorated Basic Salary (Working Days)", "working_days_salary"),
    ("Taxable Transport Allowance", "taxable_transport_allowance"),
    ("Professional Allowance", "taxable_professional_allowance"),
    ("Positional Allowance", "taxable_positional_allowance"),
    ("Acting Allowance", "acting_allowance"),
    ("Incentive Allowance", "incentive_allowance"),
    ("Overtime", "overtime"),
    ("Other Taxable Allowance", "other_taxable_allowance"),
    ("Other Taxable Allowance 2", "other_taxable_allowance_two"),
    ("Non-Taxable Transport Allowance", "nontaxable_transport_allowance"),
    ("Other Non-Taxable Allowance", "other_nontaxable_allowance"),
    ("Other Non-Taxable Allowance 2", "other_nontaxable_allowance_two"),
]

DEDUCTION_FIELDS = [(label, field) for label, field in DEDUCTION_TYPE_MAP.items()]


def pay_slip_report(filters):
    """Tabular multi-employee view by default. When exactly one employee's
    record is matched (via the Employee filter, ideally combined with
    Budget Year/Month or Document), switch to a clean payslip-style
    breakdown showing only components that actually have a value."""

    conditions, values = get_conditions(filters, parent_alias="p")
    extra = ""
    if filters.get("employee_id"):
        extra = " AND c.employee_id = %(employee_id)s"
        values["employee_id"] = filters.get("employee_id")

    rows = frappe.db.sql(
        f"""
        SELECT c.*, p.budget_year, p.budget_month
        FROM `tabEmployee Payroll Sheet` c
        INNER JOIN `tabEmployee Payroll` p ON p.name = c.parent
        WHERE c.parenttype = 'Employee Payroll' {conditions} {extra}
        ORDER BY c.employee_name
        """,
        values,
        as_dict=True,
    )

    if filters.get("employee_id") and len(rows) == 1:
        return pay_slip_single_employee(rows[0])

    if filters.get("employee_id") and len(rows) > 1:
        frappe.msgprint(
            _(
                "More than one pay record matches this employee. Add Budget "
                "Year / Budget Month / Document to narrow it down to a single "
                "payslip. Showing the standard table for now."
            )
        )

    return pay_slip_columns(), rows


def pay_slip_columns():
    return [
        {"label": _("Employee ID"), "fieldname": "employee_id", "fieldtype": "Link",
         "options": "Employee", "width": 110},
        {"label": _("Employee Name"), "fieldname": "employee_name", "fieldtype": "Data", "width": 160},
        {"label": _("Department"), "fieldname": "department", "fieldtype": "Link",
         "options": "Department", "width": 130},
        {"label": _("Designation"), "fieldname": "designation", "fieldtype": "Link",
         "options": "Designation", "width": 120},
        {"label": _("Basic Salary"), "fieldname": "basic_salary", "fieldtype": "Currency", "width": 110},
        {"label": _("Taxable Transport"), "fieldname": "taxable_transport_allowance", "fieldtype": "Currency", "width": 130},
        {"label": _("Professional Allow."), "fieldname": "taxable_professional_allowance", "fieldtype": "Currency", "width": 130},
        {"label": _("Positional Allow."), "fieldname": "taxable_positional_allowance", "fieldtype": "Currency", "width": 130},
        {"label": _("Acting Allow."), "fieldname": "acting_allowance", "fieldtype": "Currency", "width": 110},
        {"label": _("Incentive Allow."), "fieldname": "incentive_allowance", "fieldtype": "Currency", "width": 110},
        {"label": _("Overtime"), "fieldname": "overtime", "fieldtype": "Currency", "width": 100},
        {"label": _("Other Taxable Allow."), "fieldname": "other_taxable_allowance", "fieldtype": "Currency", "width": 130},
        {"label": _("Other Taxable Allow. 2"), "fieldname": "other_taxable_allowance_two", "fieldtype": "Currency", "width": 140},
        {"label": _("Non-Taxable Transport"), "fieldname": "nontaxable_transport_allowance", "fieldtype": "Currency", "width": 150},
        {"label": _("Other Non-Taxable"), "fieldname": "other_nontaxable_allowance", "fieldtype": "Currency", "width": 130},
        {"label": _("Other Non-Taxable 2"), "fieldname": "other_nontaxable_allowance_two", "fieldtype": "Currency", "width": 140},
        {"label": _("Total Taxable"), "fieldname": "total_taxable_allowance", "fieldtype": "Currency", "width": 120},
        {"label": _("Total Non-Taxable"), "fieldname": "total_non_taxable_amount", "fieldtype": "Currency", "width": 140},
        {"label": _("Total Earning"), "fieldname": "total_earning", "fieldtype": "Currency", "width": 120},
        {"label": _("Pension 7%"), "fieldname": "pension_7", "fieldtype": "Currency", "width": 100},
        {"label": _("Income Tax"), "fieldname": "income_tax", "fieldtype": "Currency", "width": 100},
        {"label": _("Total Deduction"), "fieldname": "total_deduction", "fieldtype": "Currency", "width": 130},
        {"label": _("Net Payment"), "fieldname": "net_payment", "fieldtype": "Currency", "width": 130},
    ]


def pay_slip_single_employee(row):
    """Pivoted, payslip-style output: a component/amount table containing
    only rows with an actual (non-zero) value, plus a summary header."""

    columns = [
        {"label": _("Component"), "fieldname": "component", "fieldtype": "Data", "width": 260},
        {"label": _("Amount"), "fieldname": "amount", "fieldtype": "Currency", "width": 160},
    ]

    data = []

    data.append({"component": "— " + str(_("Earnings")) + " —", "amount": None})
    for label, fieldname in EARNING_FIELDS:
        amount = flt(row.get(fieldname))
        if amount:
            data.append({"component": _(label), "amount": amount})
    data.append({"component": _("Total Earning"), "amount": flt(row.get("total_earning"))})

    data.append({"component": "— " + str(_("Deductions")) + " —", "amount": None})
    for label, fieldname in DEDUCTION_FIELDS:
        amount = flt(row.get(fieldname))
        if amount:
            data.append({"component": _(label), "amount": amount})
    data.append({"component": _("Total Deduction"), "amount": flt(row.get("total_deduction"))})

    data.append({"component": _("Net Payment"), "amount": flt(row.get("net_payment"))})

    report_summary = [
        {"value": row.get("employee_name"), "label": _("Employee"), "datatype": "Data"},
        {"value": row.get("department") or "-", "label": _("Department"), "datatype": "Data"},
        {"value": row.get("designation") or "-", "label": _("Designation"), "datatype": "Data"},
        {"value": flt(row.get("total_earning")), "label": _("Total Earning"), "datatype": "Currency"},
        {"value": flt(row.get("total_deduction")), "label": _("Total Deduction"), "datatype": "Currency"},
        {"value": flt(row.get("net_payment")), "label": _("Net Payment"), "datatype": "Currency"},
    ]

    return columns, data, None, None, report_summary


def pay_slip_summary(data):
    """Cards for the fallback multi-employee table view (used when the
    Employee filter is blank, or matches more than one record)."""
    return [
        {"value": len(data), "label": _("Employees"), "datatype": "Int"},
        {"value": sum_field(data, "total_earning"), "label": _("Total Earning"), "datatype": "Currency"},
        {"value": sum_field(data, "total_deduction"), "label": _("Total Deduction"), "datatype": "Currency"},
        {"value": sum_field(data, "net_payment"), "label": _("Total Net Payment"),
         "datatype": "Currency", "indicator": "Green"},
    ]


# ---------------------------------------------------------------------------
# 5. Pay Summary
# ---------------------------------------------------------------------------

def pay_summary_columns():
    return [
        {"label": _("Department"), "fieldname": "department", "fieldtype": "Link",
         "options": "Department", "width": 160},
        {"label": _("Employee Count"), "fieldname": "employee_count", "fieldtype": "Int", "width": 120},
        {"label": _("Total Basic Salary"), "fieldname": "total_basic_salary", "fieldtype": "Currency", "width": 150},
        {"label": _("Total Taxable Allowance"), "fieldname": "total_taxable_allowance", "fieldtype": "Currency", "width": 170},
        {"label": _("Total Non-Taxable"), "fieldname": "total_non_taxable_amount", "fieldtype": "Currency", "width": 150},
        {"label": _("Total Earning"), "fieldname": "total_earning", "fieldtype": "Currency", "width": 130},
        {"label": _("Total Pension 7%"), "fieldname": "total_pension_7", "fieldtype": "Currency", "width": 130},
        {"label": _("Total Income Tax"), "fieldname": "total_income_tax", "fieldtype": "Currency", "width": 130},
        {"label": _("Total Deduction"), "fieldname": "total_deduction", "fieldtype": "Currency", "width": 140},
        {"label": _("Total Net Payment"), "fieldname": "total_net_payment", "fieldtype": "Currency", "width": 150},
    ]


def pay_summary_data(filters):
    conditions, values = get_conditions(filters, parent_alias="p")
    return frappe.db.sql(
        f"""
        SELECT
            c.department,
            COUNT(c.name)                   AS employee_count,
            SUM(c.basic_salary)             AS total_basic_salary,
            SUM(c.total_taxable_allowance)  AS total_taxable_allowance,
            SUM(c.total_non_taxable_amount) AS total_non_taxable_amount,
            SUM(c.total_earning)            AS total_earning,
            SUM(c.pension_7)                AS total_pension_7,
            SUM(c.income_tax)               AS total_income_tax,
            SUM(c.total_deduction)          AS total_deduction,
            SUM(c.net_payment)              AS total_net_payment
        FROM `tabEmployee Payroll Sheet` c
        INNER JOIN `tabEmployee Payroll` p ON p.name = c.parent
        WHERE c.parenttype = 'Employee Payroll' {conditions}
        GROUP BY c.department
        ORDER BY c.department
        """,
        values,
        as_dict=True,
    )


def pay_summary_summary(data):
    return [
        {"value": sum_field(data, "employee_count"), "label": _("Total Employees"), "datatype": "Int"},
        {"value": len(data), "label": _("Departments"), "datatype": "Int"},
        {"value": sum_field(data, "total_earning"), "label": _("Total Earning"), "datatype": "Currency"},
        {"value": sum_field(data, "total_deduction"), "label": _("Total Deduction"), "datatype": "Currency"},
        {"value": sum_field(data, "total_net_payment"), "label": _("Total Net Payment"),
         "datatype": "Currency", "indicator": "Green"},
    ]


# ---------------------------------------------------------------------------
# 6. Data Summary
# ---------------------------------------------------------------------------
# NOTE: "Document" is kept here (unlike the other 5 views) because Data
# Summary's whole purpose is listing multiple Employee Payroll documents and
# their workflow status — without it, rows for different documents would be
# indistinguishable. Branch/Budget Year/Budget Month are dropped as requested.

def data_summary_columns():
    return [
        {"label": _("Document"), "fieldname": "document_name", "fieldtype": "Link",
         "options": "Employee Payroll", "width": 150},
        {"label": _("Employee Count"), "fieldname": "employee_count", "fieldtype": "Int", "width": 120},
        {"label": _("Fixed Fetched"), "fieldname": "fixed_components_fetched", "fieldtype": "Check", "width": 110},
        {"label": _("Variable Fetched"), "fieldname": "variable_components_fetched", "fieldtype": "Check", "width": 120},
        {"label": _("Recurring Fetched"), "fieldname": "recurring_deductions_fetched", "fieldtype": "Check", "width": 130},
        {"label": _("Attendance Fetched"), "fieldname": "attendance_fetched", "fieldtype": "Check", "width": 130},
        {"label": _("Payroll Calculated"), "fieldname": "payroll_calculated", "fieldtype": "Check", "width": 130},
        {"label": _("Total Net Payment"), "fieldname": "total_net_payment", "fieldtype": "Currency", "width": 150},
    ]


def data_summary_data(filters):
    conditions, values = get_conditions(filters, parent_alias="p")

    parent_rows = frappe.db.sql(
        f"""
        SELECT
            p.name AS document_name,
            p.fixed_components_fetched, p.variable_components_fetched,
            p.recurring_deductions_fetched, p.attendance_fetched,
            p.payroll_calculated
        FROM `tabEmployee Payroll` p
        WHERE 1 = 1 {conditions}
        ORDER BY p.creation DESC
        """,
        values,
        as_dict=True,
    )

    if not parent_rows:
        return []

    doc_names = [r.document_name for r in parent_rows]

    agg = frappe.db.sql(
        """
        SELECT
            parent AS document_name,
            COUNT(name) AS employee_count,
            SUM(net_payment) AS total_net_payment
        FROM `tabEmployee Payroll Sheet`
        WHERE parenttype = 'Employee Payroll' AND parent IN %(doc_names)s
        GROUP BY parent
        """,
        {"doc_names": doc_names},
        as_dict=True,
    )
    agg_map = {row.document_name: row for row in agg}

    for row in parent_rows:
        a = agg_map.get(row.document_name)
        row["employee_count"] = a.employee_count if a else 0
        row["total_net_payment"] = a.total_net_payment if a else 0

    return parent_rows


def data_summary_summary(data):
    fully_calculated = sum(1 for row in data if row.get("payroll_calculated"))
    return [
        {"value": len(data), "label": _("Documents"), "datatype": "Int"},
        {"value": sum_field(data, "employee_count"), "label": _("Total Employees"), "datatype": "Int"},
        {"value": fully_calculated, "label": _("Fully Calculated"), "datatype": "Int"},
        {"value": sum_field(data, "total_net_payment"), "label": _("Total Net Payment"),
         "datatype": "Currency", "indicator": "Green"},
    ]
