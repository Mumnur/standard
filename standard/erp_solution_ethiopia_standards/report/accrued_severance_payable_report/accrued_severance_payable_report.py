import frappe
from frappe.utils import getdate, date_diff


def execute(filters=None):
    filters = filters or {}

    if not filters.get("reporting_date"):
        frappe.throw("Please select Reporting Date.")

    reporting_date = getdate(filters.get("reporting_date"))

    columns = get_columns()

    employees = frappe.get_all(
        "Employee",
        fields=[
            "employee_name",
            "gender",
            "custom_birth_date_ec",
            "date_of_birth",
            "custom_date_of_joining_date_ec",
            "date_of_joining",
            "designation",
            "custom_basic_salary",
            "custom_date_ec_of_retirement",
            "date_of_retirement"
        ],
        order_by="employee_name asc"
    )

    data = []

    for employee in employees:

        # ---------------------------------------------------------
        # Dates
        # ---------------------------------------------------------

        date_of_birth = (
            getdate(employee.date_of_birth)
            if employee.date_of_birth
            else None
        )

        date_of_joining = (
            getdate(employee.date_of_joining)
            if employee.date_of_joining
            else None
        )

        date_of_retirement = (
            getdate(employee.date_of_retirement)
            if employee.date_of_retirement
            else None
        )

        basic_salary = employee.custom_basic_salary or 0

        # ---------------------------------------------------------
        # Worked Years
        # ---------------------------------------------------------

        worked_years = 0

        if date_of_joining:
            worked_years = (
                date_diff(reporting_date, date_of_joining) / 365
            )

        if worked_years < 0:
            worked_years = 0

        # ---------------------------------------------------------
        # Remaining Years
        # ---------------------------------------------------------

        remaining_years = 0

        if date_of_retirement:
            remaining_years = (
                date_diff(date_of_retirement, reporting_date) / 365
            )

        if remaining_years < 0:
            remaining_years = 0

        # ---------------------------------------------------------
        # Age
        # ---------------------------------------------------------

        age = 0

        if date_of_birth:
            age = date_diff(reporting_date, date_of_birth) / 365

        # ---------------------------------------------------------
        # Probability of Turnover
        # ---------------------------------------------------------

        probability_of_turnover = get_turnover_probability(age)

        # ---------------------------------------------------------
        # Salary Upon Retirement
        #
        # Basic Salary × (1 + 14.275%) ^ Remaining Years
        # ---------------------------------------------------------

        salary_upon_retirement = (
            basic_salary
            * ((1 + 0.14275) ** remaining_years)
        )

        # ---------------------------------------------------------
        # PV of Salary Upon Retirement
        #
        # Salary Upon Retirement × (1 + 9.5%) ^ -Remaining Years
        # ---------------------------------------------------------

        pv_salary_upon_retirement = (
            salary_upon_retirement
            * ((1 + 0.095) ** (-remaining_years))
        )

        # ---------------------------------------------------------
        # Max Allowed Period
        #
        # Maximum = 34 years
        # ---------------------------------------------------------

        max_allowed_period = min(worked_years, 34)

        if max_allowed_period < 0:
            max_allowed_period = 0

        # ---------------------------------------------------------
        # Max Entitlement Amount
        #
        # CORRECTED:
        #
        # PV Salary
        # +
        # ((Max Allowed Period - 1) / 3 × PV Salary)
        # ---------------------------------------------------------

        if max_allowed_period > 0:

            max_entitlement_amount = (
                pv_salary_upon_retirement
                + (
                    ((max_allowed_period - 1) / 3)
                    * pv_salary_upon_retirement
                )
            )

        else:
            max_entitlement_amount = 0

        # ---------------------------------------------------------
        # EV1
        #
        # Max Entitlement × Probability of Turnover
        # ---------------------------------------------------------

        ev1 = (
            max_entitlement_amount
            * probability_of_turnover
        )

        # ---------------------------------------------------------
        # Mortality Rate
        # ---------------------------------------------------------

        mortality_rate = get_mortality_rate(age)

        # ---------------------------------------------------------
        # EV2
        #
        # Max Entitlement × Mortality Rate
        # ---------------------------------------------------------

        ev2 = (
            max_entitlement_amount
            * mortality_rate
        )

        # ---------------------------------------------------------
        # Total EV
        # ---------------------------------------------------------

        total_ev = ev1 + ev2

        # ---------------------------------------------------------
        # Append Data
        # ---------------------------------------------------------

        data.append([
            employee.employee_name,
            employee.gender,
            employee.custom_birth_date_ec,
            employee.date_of_birth,
            employee.custom_date_of_joining_date_ec,
            employee.date_of_joining,
            employee.designation,
            employee.custom_basic_salary,
            employee.custom_date_ec_of_retirement,
            employee.date_of_retirement,

            worked_years,
            remaining_years,
            age,

            # Display as 1%, 2.5%, etc.
            format_percentage(probability_of_turnover),

            salary_upon_retirement,
            pv_salary_upon_retirement,
            max_allowed_period,
            max_entitlement_amount,
            ev1,

            mortality_rate,
            ev2,
            total_ev
        ])

    return columns, data


# ================================================================
# Probability of Turnover
# ================================================================

def get_turnover_probability(age):

    if age <= 25:
        return 0.15

    elif age <= 30:
        return 0.125

    elif age <= 35:
        return 0.10

    elif age <= 40:
        return 0.075

    elif age <= 45:
        return 0.05

    elif age <= 50:
        return 0.025

    elif age <= 55:
        return 0.01

    elif age <= 59.9:
        return 0.005

    else:
        return 1.00


# ================================================================
# Format Percentage
# ================================================================

def format_percentage(value):

    percentage = value * 100

    # Remove unnecessary decimal zeros
    if percentage == int(percentage):
        return f"{int(percentage)}%"

    return f"{percentage:.2f}".rstrip("0").rstrip(".") + "%"


# ================================================================
# Mortality Rate
# ================================================================

def get_mortality_rate(age):

    if age <= 20:
        return 0.00306

    elif age <= 25:
        return 0.00303

    elif age <= 30:
        return 0.00355

    elif age <= 35:
        return 0.00405

    elif age <= 40:
        return 0.00515

    elif age <= 45:
        return 0.00450

    elif age <= 50:
        return 0.00628

    elif age <= 55:
        return 0.00979

    elif age <= 60:
        return 0.01536

    else:
        return 0


# ================================================================
# Columns
# ================================================================

def get_columns():

    return [

        {
            "label": "Employee Name",
            "fieldname": "employee_name",
            "fieldtype": "Data",
            "width": 180
        },

        {
            "label": "Gender",
            "fieldname": "gender",
            "fieldtype": "Data",
            "width": 90
        },

        {
            "label": "Birth Date (EC)",
            "fieldname": "custom_birth_date_ec",
            "fieldtype": "Data",
            "width": 120
        },

        {
            "label": "Date of Birth",
            "fieldname": "date_of_birth",
            "fieldtype": "Date",
            "width": 110
        },

        {
            "label": "Joining Date (EC)",
            "fieldname": "custom_date_of_joining_date_ec",
            "fieldtype": "Data",
            "width": 120
        },

        {
            "label": "Date of Joining",
            "fieldname": "date_of_joining",
            "fieldtype": "Date",
            "width": 110
        },

        {
            "label": "Designation",
            "fieldname": "designation",
            "fieldtype": "Data",
            "width": 150
        },

        {
            "label": "Basic Salary",
            "fieldname": "custom_basic_salary",
            "fieldtype": "Currency",
            "width": 120
        },

        {
            "label": "Retirement Date (EC)",
            "fieldname": "custom_date_ec_of_retirement",
            "fieldtype": "Data",
            "width": 130
        },

        {
            "label": "Date of Retirement",
            "fieldname": "date_of_retirement",
            "fieldtype": "Date",
            "width": 120
        },

        {
            "label": "Worked Years",
            "fieldname": "worked_years",
            "fieldtype": "Float",
            "precision": 2,
            "width": 110
        },

        {
            "label": "Remaining Number of Years",
            "fieldname": "remaining_years",
            "fieldtype": "Float",
            "precision": 2,
            "width": 150
        },

        {
            "label": "Age",
            "fieldname": "age",
            "fieldtype": "Float",
            "precision": 2,
            "width": 80
        },

        {
            "label": "Probability of Turnover",
            "fieldname": "probability_of_turnover",
            "fieldtype": "Data",
            "width": 140
        },

        {
            "label": "Salary Upon Retirement",
            "fieldname": "salary_upon_retirement",
            "fieldtype": "Currency",
            "width": 160
        },

        {
            "label": "PV of Salary Upon Retirement",
            "fieldname": "pv_salary_upon_retirement",
            "fieldtype": "Currency",
            "width": 180
        },

        {
            "label": "Max Allowed Period in Years",
            "fieldname": "max_allowed_period",
            "fieldtype": "Float",
            "precision": 2,
            "width": 170
        },

        {
            "label": "Max Entitlement Amount",
            "fieldname": "max_entitlement_amount",
            "fieldtype": "Currency",
            "width": 170
        },

        {
            "label": "EV1",
            "fieldname": "ev1",
            "fieldtype": "Currency",
            "width": 140
        },

        {
            "label": "Mortality Rate",
            "fieldname": "mortality_rate",
            "fieldtype": "Percent",
            "width": 120
        },

        {
            "label": "EV2",
            "fieldname": "ev2",
            "fieldtype": "Currency",
            "width": 140
        },

        {
            "label": "Total EV",
            "fieldname": "total_ev",
            "fieldtype": "Currency",
            "width": 160
        }
    ]