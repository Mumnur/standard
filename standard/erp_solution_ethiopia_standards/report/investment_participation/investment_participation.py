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


# ============================================================
# COLUMNS
# ============================================================

def get_columns():

    return [

        {
            "label": _("Account Name"),
            "fieldname": "account_name",
            "fieldtype": "Data",
            "width": 300
        },

        {
            "label": _("Last Year Balance"),
            "fieldname": "last_year_balance",
            "fieldtype": "Currency",
            "width": 190
        },

        {
            "label": _("This Year New"),
            "fieldname": "this_year_new",
            "fieldtype": "Currency",
            "width": 190
        },

        {
            "label": _("Total Current Balance"),
            "fieldname": "total_current_balance",
            "fieldtype": "Currency",
            "width": 210
        }

    ]


# ============================================================
# GET DATA
# ============================================================

def get_data(filters):

    # ========================================================
    # GET FISCAL YEAR
    # ========================================================

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

    fy_end = getdate(
        fiscal_year.get("year_end_date")
    )

    # ========================================================
    # GET LONG-TERM INVESTMENT ACCOUNTS
    # ========================================================

    investment_accounts = frappe.get_all(
        "Account",
        filters={
            "account_category": "Long-term Investments"
        },
        fields=[
            "name",
            "account_name",
            "company",
            "is_group"
        ],
        order_by="name asc"
    )

    # ========================================================
    # ONLY LEDGER ACCOUNTS
    # ========================================================

    investment_accounts = [
        row
        for row in investment_accounts
        if not row.get("is_group")
    ]

    if not investment_accounts:
        return []

    # ========================================================
    # ACCOUNT IDs
    #
    # Used internally for GL calculations.
    # ========================================================

    account_names = [
        row.get("name")
        for row in investment_accounts
    ]

    # ========================================================
    # LAST YEAR BALANCE
    #
    # Opening balance of selected fiscal year.
    #
    # All transactions BEFORE fiscal year start.
    # ========================================================

    last_year_query = """

        SELECT

            gle.account,

            SUM(
                IFNULL(gle.debit, 0)
                -
                IFNULL(gle.credit, 0)
            ) AS last_year_balance

        FROM `tabGL Entry` gle

        WHERE

            gle.docstatus = 1

            AND gle.is_cancelled = 0

            AND gle.account IN %(accounts)s

            AND gle.posting_date < %(fy_start)s

        GROUP BY

            gle.account

    """

    last_year_data = frappe.db.sql(
        last_year_query,
        {
            "accounts": tuple(account_names),
            "fy_start": fy_start
        },
        as_dict=True
    )

    # ========================================================
    # THIS YEAR NEW
    #
    # Movement during selected fiscal year.
    # ========================================================

    this_year_query = """

        SELECT

            gle.account,

            SUM(
                IFNULL(gle.debit, 0)
                -
                IFNULL(gle.credit, 0)
            ) AS this_year_new

        FROM `tabGL Entry` gle

        WHERE

            gle.docstatus = 1

            AND gle.is_cancelled = 0

            AND gle.account IN %(accounts)s

            AND gle.posting_date >= %(fy_start)s

            AND gle.posting_date <= %(fy_end)s

        GROUP BY

            gle.account

    """

    this_year_data = frappe.db.sql(
        this_year_query,
        {
            "accounts": tuple(account_names),
            "fy_start": fy_start,
            "fy_end": fy_end
        },
        as_dict=True
    )

    # ========================================================
    # CREATE LAST YEAR MAP
    # ========================================================

    last_year_map = {}

    for row in last_year_data:

        account = row.get("account")

        last_year_map[account] = flt(
            row.get("last_year_balance")
        )

    # ========================================================
    # CREATE THIS YEAR MAP
    # ========================================================

    this_year_map = {}

    for row in this_year_data:

        account = row.get("account")

        this_year_map[account] = flt(
            row.get("this_year_new")
        )

    # ========================================================
    # BUILD FINAL DATA
    # ========================================================

    data = []

    for account in investment_accounts:

        # ----------------------------------------------------
        # INTERNAL ACCOUNT ID
        # ----------------------------------------------------

        account_id = account.get("name")

        # ----------------------------------------------------
        # DISPLAY ONLY ACCOUNT NAME
        #
        # Example:
        #
        # Account ID:
        # 15001 - Investment ABC - WWC
        #
        # Display:
        # Investment ABC
        # ----------------------------------------------------

        account_name = (
            account.get("account_name")
            or account_id
        )

        # ----------------------------------------------------
        # LAST YEAR BALANCE
        # ----------------------------------------------------

        last_year_balance = flt(
            last_year_map.get(
                account_id,
                0
            )
        )

        # ----------------------------------------------------
        # THIS YEAR NEW
        # ----------------------------------------------------

        this_year_new = flt(
            this_year_map.get(
                account_id,
                0
            )
        )

        # ----------------------------------------------------
        # TOTAL CURRENT BALANCE
        # ----------------------------------------------------

        total_current_balance = (
            last_year_balance
            +
            this_year_new
        )

        # ----------------------------------------------------
        # ADD ROW
        # ----------------------------------------------------

        data.append({

            "account_name": account_name,

            "last_year_balance":
                last_year_balance,

            "this_year_new":
                this_year_new,

            "total_current_balance":
                total_current_balance

        })

    return data


# ============================================================
# TOTAL ROW
# ============================================================

def add_total_row(data):

    if not data:
        return data

    total_last_year = 0
    total_this_year = 0
    total_current = 0

    for row in data:

        total_last_year += flt(
            row.get(
                "last_year_balance"
            )
        )

        total_this_year += flt(
            row.get(
                "this_year_new"
            )
        )

        total_current += flt(
            row.get(
                "total_current_balance"
            )
        )

    data.append({

        "account_name": _("Total"),

        "last_year_balance":
            total_last_year,

        "this_year_new":
            total_this_year,

        "total_current_balance":
            total_current,

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

        account_name = row.get(
            "account_name"
        )

        # Do not include Total in chart
        if account_name == _("Total"):
            continue

        labels.append(
            account_name
        )

        values.append(
            flt(
                row.get(
                    "total_current_balance",
                    0
                )
            )
        )

    return {

        "data": {

            "labels": labels,

            "datasets": [

                {
                    "name": _("Total Current Balance"),
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

    total_last_year = 0
    total_this_year = 0
    total_current = 0

    account_count = 0

    for row in data:

        # Skip total row
        if row.get(
            "account_name"
        ) == _("Total"):

            continue

        account_count += 1

        total_last_year += flt(
            row.get(
                "last_year_balance"
            )
        )

        total_this_year += flt(
            row.get(
                "this_year_new"
            )
        )

        total_current += flt(
            row.get(
                "total_current_balance"
            )
        )

    return [

        {
            "value": total_last_year,
            "indicator": "Blue",
            "label": _("Last Year Balance"),
            "datatype": "Currency"
        },

        {
            "value": total_this_year,
            "indicator": "Orange",
            "label": _("This Year New"),
            "datatype": "Currency"
        },

        {
            "value": total_current,
            "indicator": "Green",
            "label": _("Total Current Balance"),
            "datatype": "Currency"
        },

        {
            "value": account_count,
            "indicator": "Blue",
            "label": _("Investment Accounts"),
            "datatype": "Int"
        }

    ]