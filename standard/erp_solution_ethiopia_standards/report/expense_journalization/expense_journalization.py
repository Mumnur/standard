import frappe
from frappe import _
from frappe.utils import flt, getdate


def execute(filters=None):
    filters = frappe._dict(filters or {})

    validate_filters(filters)

    columns = get_columns()
    data = get_data(filters)

    data = add_total_row(data)

    chart = get_chart_data(data)
    summary = get_summary(data)

    return columns, data, None, chart, summary


# ============================================================
# VALIDATE FILTERS
# ============================================================

def validate_filters(filters):

    if not filters.get("fiscal_year"):
        frappe.throw(_("Fiscal Year is required."))

    if not filters.get("from_date"):
        frappe.throw(_("From Date is required."))

    if not filters.get("to_date"):
        frappe.throw(_("To Date is required."))

    from_date = getdate(filters.get("from_date"))
    to_date = getdate(filters.get("to_date"))

    if from_date > to_date:
        frappe.throw(
            _("From Date cannot be greater than To Date.")
        )

    fiscal_year = frappe.db.get_value(
        "Fiscal Year",
        filters.get("fiscal_year"),
        [
            "year_start_date",
            "year_end_date"
        ],
        as_dict=True
    )

    if not fiscal_year:
        frappe.throw(
            _("Fiscal Year {0} was not found.").format(
                filters.get("fiscal_year")
            )
        )

    fy_start = getdate(
        fiscal_year.get("year_start_date")
    )

    fy_end = getdate(
        fiscal_year.get("year_end_date")
    )

    if from_date < fy_start:
        frappe.throw(
            _(
                "From Date cannot be before Fiscal Year "
                "start date {0}."
            ).format(
                fiscal_year.get("year_start_date")
            )
        )

    if to_date > fy_end:
        frappe.throw(
            _(
                "To Date cannot be after Fiscal Year "
                "end date {0}."
            ).format(
                fiscal_year.get("year_end_date")
            )
        )


# ============================================================
# COLUMNS
# ============================================================

def get_columns():

    return [

        {
            "label": _("Company Branch"),
            "fieldname": "company_branch",
            "fieldtype": "Link",
            "options": "Company Branch",
            "width": 220
        },

        {
            "label": _("This Period Expense"),
            "fieldname": "this_period_expense",
            "fieldtype": "Currency",
            "width": 190
        },

        {
            "label": _("Up To Date Expense"),
            "fieldname": "uptodate_expense",
            "fieldtype": "Currency",
            "width": 190
        }

    ]


# ============================================================
# GET EXPENSE ACCOUNTS
# ============================================================

def get_expense_accounts():

    """
    Find all accounts belonging to:

        50000 - Cost - WWC
        60000 - Administration expense - WWC

    The report includes the parent accounts and all
    descendant accounts underneath them.
    """

    root_accounts = [
        "50000 - Cost - WWC",
        "60000 - Administration expense - WWC"
    ]

    accounts = []

    for root_account in root_accounts:

        if not frappe.db.exists(
            "Account",
            root_account
        ):
            continue

        # Include the root account itself
        accounts.append(root_account)

        descendants = frappe.db.sql(
            """
            SELECT name
            FROM `tabAccount`
            WHERE lft >= (
                SELECT lft
                FROM `tabAccount`
                WHERE name = %s
            )
            AND rgt <= (
                SELECT rgt
                FROM `tabAccount`
                WHERE name = %s
            )
            """,
            (
                root_account,
                root_account
            ),
            as_dict=True
        )

        for row in descendants:

            account = row.get("name")

            if account not in accounts:
                accounts.append(account)

    return accounts


# ============================================================
# GET DATA
# ============================================================

def get_data(filters):

    fiscal_year = frappe.db.get_value(
        "Fiscal Year",
        filters.get("fiscal_year"),
        [
            "year_start_date",
            "year_end_date"
        ],
        as_dict=True
    )

    fy_start = getdate(
        fiscal_year.get("year_start_date")
    )

    from_date = getdate(
        filters.get("from_date")
    )

    to_date = getdate(
        filters.get("to_date")
    )

    # --------------------------------------------------------
    # EXPENSE ACCOUNTS
    # --------------------------------------------------------

    expense_accounts = get_expense_accounts()

    if not expense_accounts:
        return []

    # --------------------------------------------------------
    # BASE CONDITIONS
    # --------------------------------------------------------

    conditions = [

        "gle.docstatus = 1",

        "gle.is_cancelled = 0",

        "gle.posting_date >= %(fy_start)s",

        "gle.posting_date <= %(to_date)s",

        "gle.account IN %(expense_accounts)s"

    ]

    values = {

        "fy_start": fy_start,

        "from_date": from_date,

        "to_date": to_date,

        "expense_accounts": tuple(
            expense_accounts
        )

    }

    # --------------------------------------------------------
    # COMPANY FILTER
    # --------------------------------------------------------

    if filters.get("company"):

        conditions.append(
            "gle.company = %(company)s"
        )

        values["company"] = filters.get(
            "company"
        )

    # --------------------------------------------------------
    # COMPANY BRANCH FILTER
    # --------------------------------------------------------

    if filters.get("company_branch"):

        conditions.append(
            "gle.company_branch = %(company_branch)s"
        )

        values["company_branch"] = filters.get(
            "company_branch"
        )

    base_where = " AND ".join(
        conditions
    )

    # ========================================================
    # THIS PERIOD EXPENSE
    # ========================================================

    period_query = f"""
        SELECT

            COALESCE(
                NULLIF(gle.company_branch, ''),
                'Not Set'
            ) AS company_branch,

            SUM(
                IFNULL(gle.debit, 0)
            ) AS this_period_expense

        FROM `tabGL Entry` gle

        WHERE

            {base_where}

            AND gle.posting_date >= %(from_date)s

        GROUP BY

            COALESCE(
                NULLIF(gle.company_branch, ''),
                'Not Set'
            )

        ORDER BY
            this_period_expense DESC
    """

    period_data = frappe.db.sql(
        period_query,
        values,
        as_dict=True
    )

    # ========================================================
    # UP TO DATE EXPENSE
    # ========================================================

    uptodate_query = f"""
        SELECT

            COALESCE(
                NULLIF(gle.company_branch, ''),
                'Not Set'
            ) AS company_branch,

            SUM(
                IFNULL(gle.debit, 0)
            ) AS uptodate_expense

        FROM `tabGL Entry` gle

        WHERE

            {base_where}

        GROUP BY

            COALESCE(
                NULLIF(gle.company_branch, ''),
                'Not Set'
            )
    """

    uptodate_data = frappe.db.sql(
        uptodate_query,
        values,
        as_dict=True
    )

    # ========================================================
    # CREATE MAPS
    # ========================================================

    period_map = {}

    for row in period_data:

        branch = row.get(
            "company_branch"
        )

        period_map[branch] = flt(
            row.get(
                "this_period_expense"
            )
        )

    uptodate_map = {}

    for row in uptodate_data:

        branch = row.get(
            "company_branch"
        )

        uptodate_map[branch] = flt(
            row.get(
                "uptodate_expense"
            )
        )

    # ========================================================
    # GET ALL BRANCHES
    # ========================================================

    branches = set()

    branches.update(
        period_map.keys()
    )

    branches.update(
        uptodate_map.keys()
    )

    # ========================================================
    # BUILD DATA
    # ========================================================

    data = []

    for branch in sorted(branches):

        this_period = flt(
            period_map.get(
                branch,
                0
            )
        )

        uptodate = flt(
            uptodate_map.get(
                branch,
                0
            )
        )

        data.append({

            "company_branch": branch,

            "this_period_expense": this_period,

            "uptodate_expense": uptodate

        })

    return data


# ============================================================
# TOTAL ROW
# ============================================================

def add_total_row(data):

    if not data:
        return data

    total_period = 0
    total_uptodate = 0

    for row in data:

        total_period += flt(
            row.get(
                "this_period_expense"
            )
        )

        total_uptodate += flt(
            row.get(
                "uptodate_expense"
            )
        )

    data.append({

        "company_branch": _("Total"),

        "this_period_expense": total_period,

        "uptodate_expense": total_uptodate,

        "is_total": 1

    })

    return data


# ============================================================
# DASHBOARD CHART
# ============================================================

def get_chart_data(data):

    labels = []
    values = []

    for row in data:

        branch = row.get(
            "company_branch"
        )

        if branch == _("Total"):
            continue

        labels.append(
            branch
        )

        values.append(
            flt(
                row.get(
                    "this_period_expense",
                    0
                )
            )
        )

    return {

        "data": {

            "labels": labels,

            "datasets": [

                {
                    "name": _("This Period Expense"),
                    "values": values
                }

            ]

        },

        "type": "bar",

        "height": 350,

        "colors": [
            "#2490EF"
        ]

    }


# ============================================================
# SUMMARY
# ============================================================

def get_summary(data):

    total_period = 0
    total_uptodate = 0

    branch_count = 0

    for row in data:

        if row.get(
            "company_branch"
        ) == _("Total"):

            continue

        branch_count += 1

        total_period += flt(
            row.get(
                "this_period_expense"
            )
        )

        total_uptodate += flt(
            row.get(
                "uptodate_expense"
            )
        )

    return [

        {
            "value": total_period,
            "indicator": "Red",
            "label": _("This Period Expense"),
            "datatype": "Currency"
        },

        {
            "value": total_uptodate,
            "indicator": "Orange",
            "label": _("Up To Date Expense"),
            "datatype": "Currency"
        },

        {
            "value": branch_count,
            "indicator": "Blue",
            "label": _("Company Branches"),
            "datatype": "Int"
        }

    ]