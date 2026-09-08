import frappe

from frappe import _
from frappe.utils import getdate, add_days
from erpnext.accounts.utils import get_fiscal_year


# ============================================================
# SETTINGS
# ============================================================

STAFF_RECEIVABLE_ACCOUNT = "11202-0003 - Staff Receivable - WWC"


# ============================================================
# EXECUTE
# ============================================================

def execute(filters=None):

    filters = frappe._dict(filters or {})

    validate_filters(filters)

    columns = get_columns()

    data = get_data(filters)

    chart = get_chart(data)

    return columns, data, None, chart


# ============================================================
# VALIDATION
# ============================================================

def validate_filters(filters):

    if not filters.get("reporting_date"):
        frappe.throw(
            _("Reporting Date is required")
        )


# ============================================================
# COLUMNS
# ============================================================

def get_columns():

    return [

        {
            "fieldname": "company_branch",
            "label": _("Company Branch"),
            "fieldtype": "Link",
            "options": "Company Branch",
            "width": 200,
        },

        {
            "fieldname": "last_year_ending_balance",
            "label": _("Last Year Ending Balance"),
            "fieldtype": "Currency",
            "width": 180,
        },

        {
            "fieldname": "reconciled",
            "label": _("Reconciled"),
            "fieldtype": "Currency",
            "width": 150,
        },

        {
            "fieldname": "unreconciled",
            "label": _("Unreconciled"),
            "fieldtype": "Currency",
            "width": 150,
        },

        {
            "fieldname": "current_year_balance",
            "label": _("Current Year Balance"),
            "fieldtype": "Currency",
            "width": 180,
        },

        {
            "fieldname": "total_reporting_date_balance",
            "label": _("Total Reporting Date Balance"),
            "fieldtype": "Currency",
            "width": 220,
        },

    ]


# ============================================================
# GET DATA
# ============================================================

def get_data(filters):

    reporting_date = getdate(
        filters.get("reporting_date")
    )

    # --------------------------------------------------------
    # Get Fiscal Year
    # --------------------------------------------------------

    fiscal_year_info = get_fiscal_year(
        reporting_date,
        company=None,
        as_dict=True
    )

    fiscal_year_start = getdate(
        fiscal_year_info.year_start_date
    )

    fiscal_year_end = getdate(
        fiscal_year_info.year_end_date
    )

    # Previous fiscal year closing date
    previous_year_end = add_days(
        fiscal_year_start,
        -1
    )

    # --------------------------------------------------------
    # Get GL Entries
    # --------------------------------------------------------

    gl_entries = frappe.db.sql(
        """
        SELECT

            gle.name,

            gle.company_branch,

            gle.party_type,

            gle.party,

            gle.posting_date,

            gle.debit,

            gle.credit

        FROM `tabGL Entry` gle

        WHERE

            gle.account = %(account)s

            AND gle.posting_date <= %(reporting_date)s

            AND gle.is_cancelled = 0

            AND IFNULL(gle.company_branch, '') != ''

        ORDER BY

            gle.company_branch,

            gle.party,

            gle.posting_date,

            gle.name

        """,
        {
            "account": STAFF_RECEIVABLE_ACCOUNT,
            "reporting_date": reporting_date,
        },
        as_dict=True,
    )

    # --------------------------------------------------------
    # Employee + Company Branch
    #
    # IMPORTANT:
    #
    # The key is:
    #
    #     (company_branch, employee)
    #
    # Therefore the same employee can have separate
    # receivable balances in different company branches.
    # --------------------------------------------------------

    employee_branch_data = {}

    for row in gl_entries:

        company_branch = row.company_branch or _("Not Set")

        employee = row.party or _("Unknown Employee")

        key = (
            company_branch,
            employee
        )

        if key not in employee_branch_data:

            employee_branch_data[key] = {

                "last_year_balance": 0,

                "current_year_debit": 0,

                "current_year_credit": 0,

            }

        debit = row.debit or 0

        credit = row.credit or 0

        posting_date = getdate(
            row.posting_date
        )

        # ----------------------------------------------------
        # LAST YEAR CLOSING BALANCE
        # ----------------------------------------------------

        if posting_date <= previous_year_end:

            employee_branch_data[key][
                "last_year_balance"
            ] += debit - credit

        # ----------------------------------------------------
        # CURRENT YEAR
        # ----------------------------------------------------

        elif (
            posting_date >= fiscal_year_start
            and posting_date <= reporting_date
        ):

            employee_branch_data[key][
                "current_year_debit"
            ] += debit

            employee_branch_data[key][
                "current_year_credit"
            ] += credit

    # ========================================================
    # AGGREGATE BY COMPANY BRANCH
    # ========================================================

    branch_data = {}

    for (
        company_branch,
        employee
    ), values in employee_branch_data.items():

        if company_branch not in branch_data:

            branch_data[company_branch] = {

                "last_year_ending_balance": 0,

                "reconciled": 0,

                "unreconciled": 0,

                "current_year_balance": 0,

                "total_reporting_date_balance": 0,

            }

        # ----------------------------------------------------
        # Employee opening balance
        # ----------------------------------------------------

        opening_balance = (
            values["last_year_balance"]
        )

        # ----------------------------------------------------
        # Current year transactions
        # ----------------------------------------------------

        current_year_debit = (
            values["current_year_debit"]
        )

        current_year_credit = (
            values["current_year_credit"]
        )

        # ----------------------------------------------------
        # RECONCILED
        #
        # Current-year credits first settle the previous
        # year's outstanding staff receivable.
        #
        # Example:
        #
        # Opening = 10,000
        # Credit  = 2,000
        #
        # Reconciled = 2,000
        # ----------------------------------------------------

        reconciled = min(
            current_year_credit,
            max(opening_balance, 0)
        )

        # ----------------------------------------------------
        # UNRECONCILED
        #
        # Remaining previous-year receivable.
        #
        # Example:
        #
        # Opening = 10,000
        # Reconciled = 2,000
        #
        # Unreconciled = 8,000
        # ----------------------------------------------------

        unreconciled = max(
            opening_balance - reconciled,
            0
        )

        # ----------------------------------------------------
        # Excess Credit
        #
        # If employee pays more than the opening balance,
        # the excess amount is NOT used to reduce the
        # opening balance further.
        #
        # It becomes a current-year credit.
        # ----------------------------------------------------

        excess_credit = max(
            current_year_credit - opening_balance,
            0
        )

        # ----------------------------------------------------
        # CURRENT YEAR BALANCE
        #
        # New current-year receivable
        # minus excess current-year credit.
        # ----------------------------------------------------

        current_year_balance = (
            current_year_debit
            - excess_credit
        )

        # ----------------------------------------------------
        # TOTAL REPORTING DATE BALANCE
        #
        # Remaining previous-year receivable
        # plus current-year outstanding balance.
        # ----------------------------------------------------

        total_reporting_date_balance = (
            unreconciled
            + current_year_balance
        )

        # ----------------------------------------------------
        # Add to branch totals
        # ----------------------------------------------------

        branch_data[company_branch][
            "last_year_ending_balance"
        ] += opening_balance

        branch_data[company_branch][
            "reconciled"
        ] += reconciled

        branch_data[company_branch][
            "unreconciled"
        ] += unreconciled

        branch_data[company_branch][
            "current_year_balance"
        ] += current_year_balance

        branch_data[company_branch][
            "total_reporting_date_balance"
        ] += total_reporting_date_balance

    # ========================================================
    # FINAL REPORT DATA
    # ========================================================

    data = []

    for company_branch, values in branch_data.items():

        data.append({

            "company_branch":
                company_branch,

            "last_year_ending_balance":
                values[
                    "last_year_ending_balance"
                ],

            "reconciled":
                values[
                    "reconciled"
                ],

            "unreconciled":
                values[
                    "unreconciled"
                ],

            "current_year_balance":
                values[
                    "current_year_balance"
                ],

            "total_reporting_date_balance":
                values[
                    "total_reporting_date_balance"
                ],

        })

    # --------------------------------------------------------
    # Sort by Company Branch
    # --------------------------------------------------------

    data.sort(
        key=lambda row:
            row.get("company_branch") or ""
    )

    return data


# ============================================================
# CHART
# ============================================================

def get_chart(data):

    if not data:

        return None

    labels = []

    values = []

    for row in data:

        labels.append(
            row.get("company_branch")
        )

        values.append(
            row.get(
                "total_reporting_date_balance"
            ) or 0
        )

    return {

        "data": {

            "labels": labels,

            "datasets": [

                {
                    "name":
                        _("Total Reporting Date Balance"),

                    "values":
                        values,
                }

            ],

        },

        "type": "bar",

        "height": 300,

    }