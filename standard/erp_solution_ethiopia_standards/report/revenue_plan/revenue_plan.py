import frappe
from frappe import _
from frappe.utils import flt, getdate
from datetime import date, timedelta


def execute(filters=None):
    filters = frappe._dict(filters or {})

    validate_filters(filters)

    columns = get_columns()
    data = get_data(filters)
    chart = get_chart_data(data)
    report_summary = get_report_summary(data)

    return columns, data, None, chart, report_summary


# ============================================================
# VALIDATION
# ============================================================

def validate_filters(filters):

    if not filters.get("budget_year"):
        frappe.throw(_("Please select Budget Year."))

    if not filters.get("period"):
        frappe.throw(_("Please select at least one Period."))

    periods = get_selected_periods(filters.get("period"))

    if not periods:
        frappe.throw(_("Please select at least one valid Period."))


# ============================================================
# COLUMNS
# ============================================================

def get_columns():

    return [
        {
            "label": _("Account"),
            "fieldname": "account",
            "fieldtype": "Link",
            "options": "Account",
            "width": 260,
        },
        {
            "label": _("This Period Plan"),
            "fieldname": "this_period_plan",
            "fieldtype": "Currency",
            "width": 160,
        },
        {
            "label": _("UpToDate Plan"),
            "fieldname": "uptodate_plan",
            "fieldtype": "Currency",
            "width": 160,
        },
        {
            "label": _("This Period Actual"),
            "fieldname": "this_period_actual",
            "fieldtype": "Currency",
            "width": 160,
        },
        {
            "label": _("UpToDate Actual"),
            "fieldname": "uptodate_actual",
            "fieldtype": "Currency",
            "width": 160,
        },
        {
            "label": _("This Period Performance"),
            "fieldname": "this_period_performance",
            "fieldtype": "Percent",
            "width": 180,
        },
        {
            "label": _("UpToDate Performance"),
            "fieldname": "uptodate_performance",
            "fieldtype": "Percent",
            "width": 180,
        },
    ]


# ============================================================
# DATA
# ============================================================
def get_data(filters):

    selected_periods = get_selected_periods(
        filters.get("period")
    )

    if not selected_periods:
        return []

    # Highest selected period = This Period
    latest_period = max(selected_periods)

    # --------------------------------------------------------
    # Get Budget Year
    # --------------------------------------------------------

    fiscal_start = get_fiscal_start_date(
        filters.budget_year
    )

    # --------------------------------------------------------
    # Get Revenue Plan
    #
    # IMPORTANT:
    # Accounts come ONLY from Revenue Plan.
    #
    # Therefore an account existing in GL but not planned
    # will NEVER appear in this report.
    # --------------------------------------------------------

    plan_data = get_revenue_plan_data(
        filters.budget_year,
        latest_period
    )

    if not plan_data:
        return []

    # --------------------------------------------------------
    # Period Dates
    # --------------------------------------------------------

    this_period_start, this_period_end = get_period_dates(
        fiscal_start,
        latest_period
    )

    uptodate_start = fiscal_start
    uptodate_end = this_period_end

    # --------------------------------------------------------
    # Get GL Actual
    # --------------------------------------------------------

    this_period_actuals = get_actuals_from_gl(
        this_period_start,
        this_period_end
    )

    uptodate_actuals = get_actuals_from_gl(
        uptodate_start,
        uptodate_end
    )

    # --------------------------------------------------------
    # IMPORTANT:
    #
    # ONLY use accounts from plan_data.
    #
    # Do NOT add accounts from GL.
    # --------------------------------------------------------

    accounts = set(plan_data.keys())

    data = []

    for account in sorted(accounts):

        plan = plan_data.get(
            account,
            {
                "this_period_plan": 0,
                "uptodate_plan": 0,
            }
        )

        this_period_plan = flt(
            plan.get("this_period_plan")
        )

        uptodate_plan = flt(
            plan.get("uptodate_plan")
        )

        # ----------------------------------------------------
        # Actual is only fetched for planned accounts
        # ----------------------------------------------------

        this_period_actual = flt(
            this_period_actuals.get(
                account,
                0
            )
        )

        uptodate_actual = flt(
            uptodate_actuals.get(
                account,
                0
            )
        )

        # ----------------------------------------------------
        # Performance
        # ----------------------------------------------------

        this_period_performance = 0

        if this_period_plan:
            this_period_performance = (
                this_period_actual
                / this_period_plan
            ) * 100

        uptodate_performance = 0

        if uptodate_plan:
            uptodate_performance = (
                uptodate_actual
                / uptodate_plan
            ) * 100

        data.append({
            "account": account,

            "this_period_plan": this_period_plan,
            "uptodate_plan": uptodate_plan,

            "this_period_actual": this_period_actual,
            "uptodate_actual": uptodate_actual,

            "this_period_performance":
                this_period_performance,

            "uptodate_performance":
                uptodate_performance,
        })

    return data

# ============================================================
# REVENUE PLAN DATA
# ============================================================

def get_revenue_plan_data(budget_year, latest_period):

    result = {}

    # --------------------------------------------------------
    # Parent Revenue Plan
    # --------------------------------------------------------

    plans = frappe.get_all(
        "Revenue Plan",
        filters={
            "budget_year": budget_year,
            "docstatus": ["<", 2],
        },
        fields=["name"]
    )

    if not plans:
        return result

    # --------------------------------------------------------
    # Child table
    # --------------------------------------------------------

    for plan in plans:

        rows = frappe.get_all(
            "Revenue Plan Table",
            filters={
                "parent": plan.name,
                "parenttype": "Revenue Plan",
            },
            fields=[
                "account",
                "`1`",
                "`2`",
                "`3`",
                "`4`",
                "`5`",
                "`6`",
                "`7`",
                "`8`",
                "`9`",
                "`10`",
                "`11`",
                "`12`",
            ]
        )

        for row in rows:

            account = row.account

            if not account:
                continue

            if account not in result:
                result[account] = {
                    "this_period_plan": 0,
                    "uptodate_plan": 0,
                }

            # ------------------------------------------------
            # This Period
            # ------------------------------------------------

            this_period_plan = flt(
                row.get(str(latest_period))
            )

            # ------------------------------------------------
            # UpToDate
            # Period 1 -> latest period
            # ------------------------------------------------

            uptodate_plan = 0

            for period_no in range(
                1,
                latest_period + 1
            ):
                uptodate_plan += flt(
                    row.get(str(period_no))
                )

            result[account]["this_period_plan"] += (
                this_period_plan
            )

            result[account]["uptodate_plan"] += (
                uptodate_plan
            )

    return result


# ============================================================
# GL ACTUAL
# ============================================================

def get_actuals_from_gl(from_date, to_date):

    result = {}

    if not from_date or not to_date:
        return result

    # --------------------------------------------------------
    # Revenue accounts = Income root type
    # --------------------------------------------------------

    accounts = frappe.get_all(
        "Account",
        filters={
            "root_type": "Income",
            "is_group": 0,
            "disabled": 0,
        },
        pluck="name"
    )

    if not accounts:
        return result

    # --------------------------------------------------------
    # GL Entries
    #
    # Income accounts normally have credit balance.
    #
    # Revenue actual = Credit - Debit
    # --------------------------------------------------------

    gl_entries = frappe.db.sql(
        """
        SELECT
            account,
            SUM(credit) AS credit,
            SUM(debit) AS debit

        FROM `tabGL Entry`

        WHERE
            posting_date BETWEEN %(from_date)s AND %(to_date)s

            AND account IN %(accounts)s

            AND is_cancelled = 0

        GROUP BY account

        """,
        {
            "from_date": from_date,
            "to_date": to_date,
            "accounts": tuple(accounts),
        },
        as_dict=True,
    )

    for row in gl_entries:

        actual = (
            flt(row.credit)
            - flt(row.debit)
        )

        result[row.account] = actual

    return result


# ============================================================
# INCOME ACCOUNTS
# ============================================================

def get_income_accounts(accounts):

    if not accounts:
        return set()

    income_accounts = frappe.get_all(
        "Account",
        filters={
            "name": ["in", list(accounts)],
            "root_type": "Income",
            "is_group": 0,
        },
        pluck="name"
    )

    return set(income_accounts)


# ============================================================
# ETHIOPIAN FISCAL PERIOD
# ============================================================

def get_fiscal_start_date(budget_year):

    """
    Revenue Plan fiscal year:

    Period 1:
        July 08 -> August 06

    Period 2:
        August 07 -> September 05

    Period 3:
        September 06 -> October 05

    ...

    The fiscal year starts on July 08.

    """

    # --------------------------------------------------------
    # IMPORTANT:
    #
    # Change this section according to the actual value
    # stored in your Budget Year.
    #
    # Example:
    # Budget Year = 2018/19
    #
    # Gregorian starting year = 2025
    # --------------------------------------------------------

    start_year = extract_start_year(budget_year)

    return date(
        start_year,
        7,
        8
    )

def extract_start_year(budget_year):

    """
    Supports Budget Year names such as:

        Budget Year (2026)
        2026
        2018/19
        2019/20

    Returns the Gregorian year.
    """

    import re

    value = str(budget_year).strip()

    # --------------------------------------------------------
    # Example:
    # Budget Year (2026)
    # --------------------------------------------------------

    match = re.search(r"(\d{4})", value)

    if match:
        return int(match.group(1))

    frappe.throw(
        _("Unable to determine Gregorian start year from Budget Year: {0}")
        .format(budget_year)
    )


def get_period_dates(fiscal_start, period_no):

    """
    Calculate Ethiopian/custom fiscal periods.

    Period 1:
        July 08 - August 06

    Period 2:
        August 07 - September 05

    Period 3:
        September 06 - October 05

    Each period is exactly 30 days.
    """

    if period_no < 1 or period_no > 12:
        frappe.throw(
            _("Period must be between 1 and 12.")
        )

    start_date = (
        fiscal_start
        + timedelta(
            days=(period_no - 1) * 30
        )
    )

    end_date = (
        start_date
        + timedelta(days=29)
    )

    return start_date, end_date


# ============================================================
# PERIOD FILTER
# ============================================================

def get_selected_periods(period_filter):

    if not period_filter:
        return []

    # --------------------------------------------------------
    # MultiSelect may arrive as:
    #
    # "1,2,3"
    #
    # or
    #
    # ["1", "2", "3"]
    # --------------------------------------------------------

    if isinstance(period_filter, str):

        period_filter = period_filter.replace(
            "\n",
            ","
        )

        values = period_filter.split(",")

    elif isinstance(period_filter, list):

        values = period_filter

    else:
        values = [period_filter]

    periods = []

    for value in values:

        value = str(value).strip()

        if not value:
            continue

        try:

            period = int(value)

            if 1 <= period <= 12:
                periods.append(period)

        except Exception:
            continue

    return sorted(
        list(set(periods))
    )


# ============================================================
# SUMMARY
# ============================================================

def get_report_summary(data):

    total_this_period_plan = 0
    total_uptodate_plan = 0

    total_this_period_actual = 0
    total_uptodate_actual = 0

    for row in data:

        total_this_period_plan += flt(
            row.get("this_period_plan")
        )

        total_uptodate_plan += flt(
            row.get("uptodate_plan")
        )

        total_this_period_actual += flt(
            row.get("this_period_actual")
        )

        total_uptodate_actual += flt(
            row.get("uptodate_actual")
        )

    this_period_performance = 0

    if total_this_period_plan:
        this_period_performance = (
            total_this_period_actual
            / total_this_period_plan
        ) * 100

    uptodate_performance = 0

    if total_uptodate_plan:
        uptodate_performance = (
            total_uptodate_actual
            / total_uptodate_plan
        ) * 100

    return [
        {
            "value": total_this_period_plan,
            "indicator": "blue",
            "label": _("This Period Plan"),
            "datatype": "Currency",
        },
        {
            "value": total_this_period_actual,
            "indicator": "green",
            "label": _("This Period Actual"),
            "datatype": "Currency",
        },
        {
            "value": this_period_performance,
            "indicator": "orange",
            "label": _("This Period Performance"),
            "datatype": "Percent",
        },
        {
            "value": total_uptodate_plan,
            "indicator": "blue",
            "label": _("UpToDate Plan"),
            "datatype": "Currency",
        },
        {
            "value": total_uptodate_actual,
            "indicator": "green",
            "label": _("UpToDate Actual"),
            "datatype": "Currency",
        },
        {
            "value": uptodate_performance,
            "indicator": "orange",
            "label": _("UpToDate Performance"),
            "datatype": "Percent",
        },
    ]


# ============================================================
# CHART
# ============================================================

def get_chart_data(data):

    labels = []
    plan_values = []
    actual_values = []

    for row in data:

        labels.append(
            row.get("account")
        )

        plan_values.append(
            flt(row.get("uptodate_plan"))
        )

        actual_values.append(
            flt(row.get("uptodate_actual"))
        )

    return {
        "data": {
            "labels": labels,
            "datasets": [
                {
                    "name": _("UpToDate Plan"),
                    "values": plan_values,
                },
                {
                    "name": _("UpToDate Actual"),
                    "values": actual_values,
                },
            ],
        },
        "type": "bar",
        "height": 350,
        "colors": [
            "#5e64ff",
            "#28a745",
        ],
    }