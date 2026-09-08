import frappe
from frappe import _


def execute(filters=None):

    filters = frappe._dict(filters or {})

    report_type = (
        filters.get("report_type")
        or "Payroll Summary"
    )

    # ============================================================
    # COLUMNS
    # ============================================================

    columns = get_columns(report_type)

    # ============================================================
    # DATA
    # ============================================================

    data = get_data(
        filters,
        report_type
    )

    # ============================================================
    # CHART
    # ============================================================

    chart = get_chart(
        data,
        report_type
    )

    # ============================================================
    # REPORT SUMMARY
    # ============================================================

    report_summary = get_report_summary(
        data,
        report_type
    )

    # ============================================================
    # MESSAGE
    # ============================================================

    message = get_report_message(
        filters,
        report_type
    )

    return (
        columns,
        data,
        message,
        chart,
        report_summary
    )


# ================================================================
# GET COLUMNS
# ================================================================

def get_columns(report_type):

    # ============================================================
    # PAYROLL SUMMARY
    # ============================================================

    if report_type == "Payroll Summary":

        return [

            {
                "label": _("Employee ID"),
                "fieldname": "labor_id",
                "fieldtype": "Link",
                "options": "Daily Labor Employee",
                "width": 120
            },

            {
                "label": _("Employee Name"),
                "fieldname": "full_name",
                "fieldtype": "Data",
                "width": 180
            },

            {
                "label": _("Position"),
                "fieldname": "position",
                "fieldtype": "Data",
                "width": 140
            },

            {
                "label": _("Project"),
                "fieldname": "project",
                "fieldtype": "Link",
                "options": "Project",
                "width": 140
            },

            {
                "label": _("Skill Type"),
                "fieldname": "skill_type",
                "fieldtype": "Data",
                "width": 120
            },

            {
                "label": _("Bank Account"),
                "fieldname": "account_no",
                "fieldtype": "Data",
                "width": 160
            },

            {
                "label": _("Salary / Day"),
                "fieldname": "salary_per_day",
                "fieldtype": "Currency",
                "width": 120
            },

            {
                "label": _("Working Days"),
                "fieldname": "working_days",
                "fieldtype": "Float",
                "precision": 2,
                "width": 110
            },

            {
                "label": _("Gross Salary"),
                "fieldname": "total_gross_salary",
                "fieldtype": "Currency",
                "width": 130
            },

            {
                "label": _("Income Tax"),
                "fieldname": "income_tax",
                "fieldtype": "Currency",
                "width": 120
            },

            {
                "label": _("Pension"),
                "fieldname": "pension",
                "fieldtype": "Currency",
                "width": 120
            },

            {
                "label": _("Net Payment"),
                "fieldname": "net_payment",
                "fieldtype": "Currency",
                "width": 130
            }

        ]


    # ============================================================
    # BANK FINAL
    # ============================================================

    return [

        {
            "label": _("Employee ID"),
            "fieldname": "labor_id",
            "fieldtype": "Link",
            "options": "Daily Labor Employee",
            "width": 140
        },

        {
            "label": _("Employee Name"),
            "fieldname": "full_name",
            "fieldtype": "Data",
            "width": 220
        },

        {
            "label": _("Bank Account"),
            "fieldname": "account_no",
            "fieldtype": "Data",
            "width": 200
        },

        {
            "label": _("Net Payment"),
            "fieldname": "net_payment",
            "fieldtype": "Currency",
            "width": 160
        }

    ]


# ================================================================
# GET DATA
# ================================================================

def get_data(filters, report_type):

    conditions = []
    values = {}

    # ============================================================
    # Daily Labor Salary
    # ============================================================

    if filters.get("daily_labor_salary"):

        conditions.append(
            "dls.name = %(daily_labor_salary)s"
        )

        values["daily_labor_salary"] = (
            filters.get("daily_labor_salary")
        )


    # ============================================================
    # Budget Month
    # ============================================================

    if filters.get("budget_month"):

        conditions.append(
            "dls.budget_month = %(budget_month)s"
        )

        values["budget_month"] = (
            filters.get("budget_month")
        )


    # ============================================================
    # Budget Year
    # ============================================================

    if filters.get("budget_year"):

        conditions.append(
            "dls.budget_year = %(budget_year)s"
        )

        values["budget_year"] = (
            filters.get("budget_year")
        )


    # ============================================================
    # WHERE
    # ============================================================

    where_clause = ""

    if conditions:

        where_clause = (
            "WHERE "
            + " AND ".join(conditions)
        )


    # ============================================================
    # PAYROLL SUMMARY
    # ============================================================

    if report_type == "Payroll Summary":

        data = frappe.db.sql(
            f"""
            SELECT

                child.labor_id
                    AS labor_id,

                child.full_name
                    AS full_name,

                child.position
                    AS position,

                child.project
                    AS project,

                child.skill_type
                    AS skill_type,

                child.account_no
                    AS account_no,

                child.salary_per_day
                    AS salary_per_day,

                child.working_days
                    AS working_days,

                child.total_gross_salary
                    AS total_gross_salary,

                child.income_tax
                    AS income_tax,

                child.pension
                    AS pension,

                child.net_payment
                    AS net_payment

            FROM
                `tabDaily Labor Salary` dls

            INNER JOIN
                `tabDaily Labor Salary Table` child
                ON child.parent = dls.name

            {where_clause}

            ORDER BY
                child.full_name ASC
            """,

            values,

            as_dict=True
        )


        # --------------------------------------------------------
        # Total Row
        # --------------------------------------------------------

        add_total_row(
            data,
            "Payroll Summary"
        )


        return data


    # ============================================================
    # BANK FINAL
    # ============================================================

    data = frappe.db.sql(
        f"""
        SELECT

            child.labor_id
                AS labor_id,

            child.full_name
                AS full_name,

            child.account_no
                AS account_no,

            child.net_payment
                AS net_payment

        FROM
            `tabDaily Labor Salary` dls

        INNER JOIN
            `tabDaily Labor Salary Table` child
            ON child.parent = dls.name

        {where_clause}

        AND IFNULL(child.account_no, '') != ''

        AND IFNULL(child.net_payment, 0) > 0

        ORDER BY
            child.full_name ASC
        """,

        values,

        as_dict=True
    )


    # ------------------------------------------------------------
    # Total Bank Payment
    # ------------------------------------------------------------

    add_total_row(
        data,
        "Bank Final"
    )


    return data


# ================================================================
# ADD TOTAL ROW
# ================================================================

def add_total_row(data, report_type):

    if not data:
        return


    if report_type == "Payroll Summary":

        total_row = {

            "labor_id": "",

            "full_name":
                "<b>Total</b>",

            "position": "",

            "project": "",

            "skill_type": "",

            "account_no": "",

            "salary_per_day": 0,

            "working_days": 0,

            "total_gross_salary": 0,

            "income_tax": 0,

            "pension": 0,

            "net_payment": 0
        }


        for row in data:

            total_row["working_days"] += (
                row.get("working_days") or 0
            )

            total_row["total_gross_salary"] += (
                row.get("total_gross_salary") or 0
            )

            total_row["income_tax"] += (
                row.get("income_tax") or 0
            )

            total_row["pension"] += (
                row.get("pension") or 0
            )

            total_row["net_payment"] += (
                row.get("net_payment") or 0
            )


        data.append(total_row)


    else:

        total_payment = 0

        for row in data:

            total_payment += (
                row.get("net_payment") or 0
            )


        data.append({

            "labor_id": "",

            "full_name":
                "<b>Total Bank Payment</b>",

            "account_no": "",

            "net_payment":
                total_payment
        })


# ================================================================
# REPORT SUMMARY
# ================================================================

def get_report_summary(data, report_type):

    if not data:
        return []


    # Remove total row
    actual_rows = data[:-1]


    # ============================================================
    # PAYROLL SUMMARY
    # ============================================================

    if report_type == "Payroll Summary":

        employee_count = len(
            actual_rows
        )


        total_working_days = sum(
            row.get("working_days") or 0
            for row in actual_rows
        )


        total_gross = sum(
            row.get("total_gross_salary") or 0
            for row in actual_rows
        )


        total_tax = sum(
            row.get("income_tax") or 0
            for row in actual_rows
        )


        total_pension = sum(
            row.get("pension") or 0
            for row in actual_rows
        )


        total_net = sum(
            row.get("net_payment") or 0
            for row in actual_rows
        )


        return [

            {
                "value": employee_count,
                "indicator": "Blue",
                "label": _("Employees"),
                "datatype": "Int"
            },

            {
                "value": round(
                    total_working_days,
                    2
                ),
                "indicator": "Blue",
                "label": _("Total Working Days"),
                "datatype": "Float"
            },

            {
                "value": total_gross,
                "indicator": "Orange",
                "label": _("Gross Salary"),
                "datatype": "Currency"
            },

            {
                "value": total_tax,
                "indicator": "Red",
                "label": _("Income Tax"),
                "datatype": "Currency"
            },

            {
                "value": total_pension,
                "indicator": "Red",
                "label": _("Pension"),
                "datatype": "Currency"
            },

            {
                "value": total_net,
                "indicator": "Green",
                "label": _("Net Payment"),
                "datatype": "Currency"
            }

        ]


    # ============================================================
    # BANK FINAL
    # ============================================================

    employee_count = len(
        actual_rows
    )


    employees_with_account = sum(
        1
        for row in actual_rows
        if row.get("account_no")
    )


    total_bank_payment = sum(
        row.get("net_payment") or 0
        for row in actual_rows
    )


    return [

        {
            "value": employee_count,
            "indicator": "Blue",
            "label": _("Employees"),
            "datatype": "Int"
        },

        {
            "value": employees_with_account,
            "indicator": "Blue",
            "label": _("Bank Accounts"),
            "datatype": "Int"
        },

        {
            "value": total_bank_payment,
            "indicator": "Green",
            "label": _("Total Bank Payment"),
            "datatype": "Currency"
        }

    ]


# ================================================================
# CHART
# ================================================================

def get_chart(data, report_type):

    if not data:
        return None


    # Remove total row
    rows = data[:-1]


    # ============================================================
    # PAYROLL SUMMARY CHART
    # ============================================================

    if report_type == "Payroll Summary":

        total_gross = sum(
            row.get("total_gross_salary") or 0
            for row in rows
        )


        total_tax = sum(
            row.get("income_tax") or 0
            for row in rows
        )


        total_pension = sum(
            row.get("pension") or 0
            for row in rows
        )


        total_net = sum(
            row.get("net_payment") or 0
            for row in rows
        )


        return {

            "data": {

                "labels": [
                    _("Gross Salary"),
                    _("Income Tax"),
                    _("Pension"),
                    _("Net Payment")
                ],

                "datasets": [

                    {
                        "name": _("Payroll"),
                        "values": [
                            total_gross,
                            total_tax,
                            total_pension,
                            total_net
                        ]
                    }

                ]

            },

            "type": "bar",

            "height": 300

        }


    # ============================================================
    # BANK FINAL CHART
    # ============================================================

    total_bank_payment = sum(
        row.get("net_payment") or 0
        for row in rows
    )


    employee_count = len(rows)


    return {

        "data": {

            "labels": [
                _("Employees"),
                _("Total Bank Payment")
            ],

            "datasets": [

                {
                    "name": _("Bank Final"),
                    "values": [
                        employee_count,
                        total_bank_payment
                    ]
                }

            ]

        },

        "type": "bar",

        "height": 300
    }


# ================================================================
# REPORT MESSAGE
# ================================================================

def get_report_message(filters, report_type):

    parts = []


    # ============================================================
    # REPORT TITLE
    # ============================================================

    if report_type == "Bank Final":

        parts.append(
            "<b>"
            + _("DAILY LABOR BANK FINAL")
            + "</b>"
        )

    else:

        parts.append(
            "<b>"
            + _("DAILY LABOR PAYROLL SUMMARY")
            + "</b>"
        )


    # ============================================================
    # BUDGET MONTH
    # ============================================================

    if filters.get("budget_month"):

        parts.append(
            _("Budget Month: {0}").format(
                frappe.bold(
                    filters.get("budget_month")
                )
            )
        )


    # ============================================================
    # BUDGET YEAR
    # ============================================================

    if filters.get("budget_year"):

        parts.append(
            _("Budget Year: {0}").format(
                frappe.bold(
                    filters.get("budget_year")
                )
            )
        )


    # ============================================================
    # DAILY LABOR SALARY
    # ============================================================

    if filters.get("daily_labor_salary"):

        parts.append(
            _("Daily Labor Salary: {0}").format(
                frappe.bold(
                    filters.get("daily_labor_salary")
                )
            )
        )


    return "<br>".join(parts)
