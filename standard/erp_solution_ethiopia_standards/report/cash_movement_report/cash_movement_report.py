import frappe
from frappe import _
from frappe.utils import flt, getdate


# ============================================================
# EXECUTE
# ============================================================

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
        frappe.throw(
            _("Fiscal Year is required.")
        )

    if not filters.get("from_date"):
        frappe.throw(
            _("From Date is required.")
        )

    if not filters.get("to_date"):
        frappe.throw(
            _("To Date is required.")
        )

    from_date = getdate(
        filters.get("from_date")
    )

    to_date = getdate(
        filters.get("to_date")
    )

    if from_date > to_date:
        frappe.throw(
            _("From Date cannot be greater than To Date.")
        )

    # --------------------------------------------------------
    # Get Fiscal Year
    # --------------------------------------------------------

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

    # --------------------------------------------------------
    # Validate From Date
    # --------------------------------------------------------

    if from_date < fy_start:

        frappe.throw(
            _(
                "From Date cannot be before Fiscal Year start date {0}."
            ).format(
                fiscal_year.get("year_start_date")
            )
        )

    # --------------------------------------------------------
    # Validate To Date
    # --------------------------------------------------------

    if to_date > fy_end:

        frappe.throw(
            _(
                "To Date cannot be after Fiscal Year end date {0}."
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
            "label": _("Transaction Date"),
            "fieldname": "transaction_date",
            "fieldtype": "Date",
            "width": 130
        },

        {
            "label": _("From Branch"),
            "fieldname": "from_banch",
            "fieldtype": "Link",
            "options": "Company Branch",
            "width": 220
        },

        {
            "label": _("To Branch"),
            "fieldname": "to_banch",
            "fieldtype": "Link",
            "options": "Company Branch",
            "width": 220
        },

        {
            "label": _("Amount"),
            "fieldname": "amount",
            "fieldtype": "Currency",
            "width": 180
        }

    ]


# ============================================================
# GET DATA
# ============================================================

def get_data(filters):

    conditions = [
        "cm.docstatus = 1",
        "cm.transaction_date >= %(from_date)s",
        "cm.transaction_date <= %(to_date)s"
    ]

    values = {

        "from_date": getdate(
            filters.get("from_date")
        ),

        "to_date": getdate(
            filters.get("to_date")
        )

    }

    # ========================================================
    # FROM BRANCH FILTER
    # ========================================================

    if filters.get("from_banch"):

        conditions.append(
            """
            cmt.from_banch = %(from_banch)s
            """
        )

        values["from_banch"] = filters.get(
            "from_banch"
        )

    # ========================================================
    # TO BRANCH FILTER
    # ========================================================

    if filters.get("to_banch"):

        conditions.append(
            """
            cmt.to_banch = %(to_banch)s
            """
        )

        values["to_banch"] = filters.get(
            "to_banch"
        )

    # ========================================================
    # QUERY
    # ========================================================

    query = f"""

        SELECT

            cm.transaction_date
                AS transaction_date,

            COALESCE(
                NULLIF(
                    cmt.from_banch,
                    ''
                ),
                'Not Set'
            ) AS from_banch,

            COALESCE(
                NULLIF(
                    cmt.to_banch,
                    ''
                ),
                'Not Set'
            ) AS to_banch,

            SUM(
                IFNULL(
                    cmt.amount,
                    0
                )
            ) AS amount

        FROM
            `tabCash Movement` cm

        INNER JOIN
            `tabCash Movement Table` cmt
                ON cmt.parent = cm.name

        WHERE
            {" AND ".join(conditions)}

        GROUP BY

            cm.transaction_date,

            cmt.from_banch,

            cmt.to_banch

        ORDER BY

            cm.transaction_date ASC,

            cmt.from_banch ASC,

            cmt.to_banch ASC

    """

    data = frappe.db.sql(
        query,
        values,
        as_dict=True
    )

    # ========================================================
    # FORMAT DATA
    # ========================================================

    result = []

    for row in data:

        result.append({

            "transaction_date":
                row.get(
                    "transaction_date"
                ),

            "from_banch":
                row.get(
                    "from_banch"
                ),

            "to_banch":
                row.get(
                    "to_banch"
                ),

            "amount":
                flt(
                    row.get(
                        "amount"
                    )
                )

        })

    return result


# ============================================================
# TOTAL ROW
# ============================================================

def add_total_row(data):

    if not data:
        return data

    total_amount = 0

    for row in data:

        total_amount += flt(
            row.get(
                "amount"
            )
        )

    data.append({

        "transaction_date":
            None,

        "from_banch":
            _("Total"),

        "to_banch":
            "",

        "amount":
            total_amount,

        "is_total":
            1

    })

    return data


# ============================================================
# DASHBOARD CHART
# ============================================================

def get_chart_data(data):

    labels = []
    values = []

    for row in data:

        if row.get("is_total"):
            continue

        label = "{} → {}".format(
            row.get("from_banch") or "Not Set",
            row.get("to_banch") or "Not Set"
        )

        labels.append(label)

        values.append(
            flt(
                row.get(
                    "amount",
                    0
                )
            )
        )

    return {

        "data": {

            "labels":
                labels,

            "datasets": [

                {
                    "name":
                        _("Cash Movement"),

                    "values":
                        values
                }

            ]

        },

        "type":
            "bar",

        "height":
            350,

        "colors": [
            "#2490EF"
        ]

    }


# ============================================================
# REPORT SUMMARY
# ============================================================

def get_summary(data):

    total_amount = 0
    transaction_count = 0

    for row in data:

        if row.get("is_total"):
            continue

        transaction_count += 1

        total_amount += flt(
            row.get(
                "amount"
            )
        )

    return [

        {
            "value":
                total_amount,

            "indicator":
                "Blue",

            "label":
                _("Total Cash Movement"),

            "datatype":
                "Currency"
        },

        {
            "value":
                transaction_count,

            "indicator":
                "Green",

            "label":
                _("Cash Movements"),

            "datatype":
                "Int"
        }

    ]