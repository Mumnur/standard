# Copyright (c) 2026, Muhammed Nurhusien
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import flt


INCOME_TAX_SLABS = [
    (0, 2000, 0.00, 0.00),
    (2001, 4000, 0.15, 300.00),
    (4001, 7000, 0.20, 500.00),
    (7001, 10000, 0.25, 850.00),
    (10001, 14000, 0.30, 1350.00),
    (14001, float("inf"), 0.35, 2050.00),
]

TAXABLE_ALLOWANCE_FIELDS = [
    "taxable_transport_allowance",
    "working_days_salary",
    "overtime",
    "taxable_professional_allowance",
    "other_taxable_allowance",
    "taxable_positional_allowance",
    "other_taxable_allowance_two",
    "acting_allowance",
    "incentive_allowance",
]

NON_TAXABLE_ALLOWANCE_FIELDS = [
    "nontaxable_transport_allowance",
    "other_nontaxable_allowance",
    "other_nontaxable_allowance_two",
]

OTHER_DEDUCTION_FIELDS = [
    "credit_association_awwce",
    "ada",
    "edir",
    "aids_fund",
    "andm",
    "cost_sharing",
    "red_cross",
    "operator_association",
    "abay_dam",
    "credit_association_drilling",
    "shemachoche",
    "defense_contribution",
    "other_one",
    "other_two",
    "other_three",
    "penalty_deduction",
    "advance_deduction",
    "other_variable_deduction_one",
    "other_variable_deduction_two",
    "recurring_deduction_one",
    "recurring_deduction_two",
]


def calculate_income_tax(taxable_amount):
    taxable_amount = flt(taxable_amount)
    for lower, upper, rate, deduction in INCOME_TAX_SLABS:
        if lower <= taxable_amount <= upper:
            tax = taxable_amount * rate - deduction
            return tax if tax > 0 else 0
    return 0


def calculate_row(row):
    """Compute all derived payroll fields on a single
    Employee Payroll Sheet child row, in place."""

    basic_salary = flt(row.basic_salary)
    working_days = flt(row.working_days)

    row.working_days_salary = basic_salary * working_days / 30

    row.total_taxable_allowance = sum(
        flt(row.get(f)) for f in TAXABLE_ALLOWANCE_FIELDS
    )
    row.total_non_taxable_amount = sum(
        flt(row.get(f)) for f in NON_TAXABLE_ALLOWANCE_FIELDS
    )
    row.total_earning = row.total_taxable_allowance + row.total_non_taxable_amount

    row.pension_7 = basic_salary * 0.07
    row.pension_11 = basic_salary * 0.11

    row.income_tax = calculate_income_tax(row.total_taxable_allowance)

    other_deductions = sum(
        flt(row.get(f)) for f in OTHER_DEDUCTION_FIELDS
    )
    row.total_deduction = row.pension_7 + row.income_tax + other_deductions

    row.net_payment = row.total_earning - row.total_deduction


class EmployeePayroll(Document):

    def validate(self):
        for row in self.employee_payroll_sheet:
            calculate_row(row)


def chunks(items, size=500):
    """Yield successive chunks of `items`. Keeps IN-clauses from getting
    too large when there are thousands of employees."""
    items = list(items)
    for i in range(0, len(items), size):
        yield items[i:i + size]


@frappe.whitelist()
def fetch_employee_information(company_branch=None):

    filters = {
        "status": "Active"
    }

    if company_branch:
        filters["custom_branch"] = company_branch

    return frappe.get_all(
        "Employee",
        filters=filters,
        fields=[
            "name",
            "employee_name",
            "custom_branch",
            "department",
            "payroll_cost_center",
            "custom_project",
            "employment_type",
            "designation",
            "custom_date_of_joining_date_ec",
            "date_of_joining",
            "custom_tin_number",
            "custom_pension_number",
            "custom_pension"
        ],
        order_by="employee_name",
        limit_page_length=0  
    )


@frappe.whitelist()
def fetch_fixed_salary_components(employees):

    if isinstance(employees, str):
        employees = frappe.parse_json(employees)

    if not employees:
        return {}

    result = {}

    for batch in chunks(employees):
        records = frappe.get_all(
            "Fixed Salary Component",
            filters={
                "employee_id": ["in", batch]
            },
            fields=[
                "employee_id",
                "bank_ac_no",
                "basic_salary",
                "taxable_transport_allowance",
                "taxable_professional_allowance",
                "other_taxable_allowance",
                "taxable_positional_allowance",
                "nontaxable_transport_allowance",
                "other_nontaxable_allowance",
                "credit_association",
                "ada",
                "edir",
                "aids_fund",
                "andm",
                "cost_sharing",
                "red_cross",
                "operator_association",
                "abay_dam",
                "credit_association_rig",
                "shemachoche",
                "defense_contribution",
                "other_one",
                "other_two",
                "other_three"
            ],
            limit_page_length=0
        )
        for row in records:
            result[row.employee_id] = row

    return result


@frappe.whitelist()
def fetch_variable_salary_components(employees, budget_year, budget_month):

    if isinstance(employees, str):
        employees = frappe.parse_json(employees)

    if not employees:
        return {}

    result = {}

    for batch in chunks(employees):
        records = frappe.get_all(
            "Variable Salary Component",
            filters={
                "employee_id": ["in", batch],
                "budget_year": budget_year,
                "budget_month": budget_month
            },
            fields=[
                "employee_id",
                "acting_allowance",
                "incentive_allowance",
                "other_taxable_allowance",
                "other_nontaxable_allowance",
                "penalty_deduction",
                "advance_deduction",
                "other_variable_deduction_one",
                "other_variable_deduction_two"
            ],
            limit_page_length=0
        )
        for row in records:
            result[row.employee_id] = row

    return result


@frappe.whitelist()
def fetch_recurring_deduction_components(employees, budget_year, budget_month):

    if isinstance(employees, str):
        employees = frappe.parse_json(employees)

    if not employees:
        return {}

    result = {}
    CHILD_DOCTYPE = "Recurring Payroll Deduction Table"  
    for batch in chunks(employees):

        deductions = frappe.get_all(
            "Recurring Payroll Deduction",
            filters={"employee_id": ["in", batch]},
            fields=["name", "employee_id", "recurring_deduction_type"],
            limit_page_length=0
        )

        if not deductions:
            continue

        parent_map = {
            d.name: (d.employee_id, d.recurring_deduction_type)
            for d in deductions
        }
        parent_names = list(parent_map.keys())

        for parent_batch in chunks(parent_names):

            rows = frappe.get_all(
                CHILD_DOCTYPE,
                filters={
                    "parent": ["in", parent_batch],
                    "year": budget_year,
                    "month": budget_month
                },
                fields=["parent", "amount"],
                limit_page_length=0
            )

            for row in rows:
                employee_id, deduction_type = parent_map.get(row.parent, (None, None))
                if not employee_id:
                    continue

                if employee_id not in result:
                    result[employee_id] = {
                        "recurring_deduction_one": 0,
                        "recurring_deduction_two": 0
                    }

                if deduction_type == "Recurring Deduction One":
                    result[employee_id]["recurring_deduction_one"] = row.amount
                elif deduction_type == "Recurring Deduction Two":
                    result[employee_id]["recurring_deduction_two"] = row.amount

    return result


@frappe.whitelist()
def fetch_attendance_and_overtime(employees, budget_year, budget_month):

    if isinstance(employees, str):
        employees = frappe.parse_json(employees)

    if not employees:
        return {}

    result = {}
    CHILD_DOCTYPE = "Employee Attendance Table" 

    overtime_amount = frappe.db.get_value(
        "Over Time",
        {
            "budget_year": budget_year,
            "month": budget_month
        },
        "overtime_amount"
    ) or 0

    attendance_parent = frappe.db.get_value(
        "Employee Attendance",
        {
            "budget_year": budget_year,
            "budget_month": budget_month
        },
        "name"
    )

    if not attendance_parent:
        return result

    for batch in chunks(employees):

        rows = frappe.get_all(
            CHILD_DOCTYPE,
            filters={
                "parent": attendance_parent,
                "employee_id": ["in", batch]
            },
            fields=["employee_id", "working_days"],
            limit_page_length=0
        )

        for row in rows:
            result[row.employee_id] = {
                "working_days": row.working_days,
                "overtime": overtime_amount
            }

    return result