import frappe


def execute(filters=None):

    filters = filters or {}

    columns = get_columns(filters)
    data = get_data(filters)
    chart = get_chart_data(filters)
    summary = get_summary(filters)

    return columns, data, None, chart, summary


# ============================================================
# COLUMNS
# ============================================================

def get_columns(filters):

    report_type = filters.get("report_type")

    # ========================================================
    # EMPLOYEE INCOME TAX
    # ========================================================

    if report_type == "Employee Income Tax":

        return [

            {
                "fieldname": "employee_id",
                "label": "Employee ID",
                "fieldtype": "Data",
                "width": 130
            },

            {
                "fieldname": "employee_name",
                "label": "Employee Name",
                "fieldtype": "Data",
                "width": 180
            },

            {
                "fieldname": "tin_number",
                "label": "TIN Number",
                "fieldtype": "Data",
                "width": 140
            },

            {
                "fieldname": "date_of_joining_ec",
                "label": "Date of Joining E.C",
                "fieldtype": "Data",
                "width": 140
            },

            {
                "fieldname": "date_of_joining",
                "label": "Date of Joining G.C",
                "fieldtype": "Date",
                "width": 130
            },

            {
                "fieldname": "basic_salary",
                "label": "Basic Salary",
                "fieldtype": "Currency",
                "width": 130
            },

            {
                "fieldname": "transport_allowance",
                "label": "Transport Allowance",
                "fieldtype": "Currency",
                "width": 150
            },

            {
                "fieldname": "total_non_taxable_amount",
                "label": "Total Non-Taxable Amount",
                "fieldtype": "Currency",
                "width": 170
            },

            {
                "fieldname": "taxable_transport_allowance",
                "label": "Taxable Transport Allowance",
                "fieldtype": "Currency",
                "width": 180
            },

            {
                "fieldname": "overtime",
                "label": "Overtime",
                "fieldtype": "Currency",
                "width": 120
            },

            {
                "fieldname": "other_taxable_allowance",
                "label": "Other Taxable Allowance",
                "fieldtype": "Currency",
                "width": 170
            },

            {
                "fieldname": "total_taxable_allowance",
                "label": "Total Taxable Allowance",
                "fieldtype": "Currency",
                "width": 170
            },

            {
                "fieldname": "income_tax",
                "label": "Income Tax",
                "fieldtype": "Currency",
                "width": 130
            },

            {
                "fieldname": "cost_sharing",
                "label": "Cost Sharing",
                "fieldtype": "Currency",
                "width": 130
            }

        ]


    # ========================================================
    # SALES OF BID
    # ========================================================

    if report_type == "Sales of Bid":

        return [

            {
                "fieldname": "tin_nos",
                "label": "TIN No",
                "fieldtype": "Data",
                "width": 140
            },

            {
                "fieldname": "name1",
                "label": "Name",
                "fieldtype": "Data",
                "width": 200
            },

            {
                "fieldname": "descriptions",
                "label": "Description",
                "fieldtype": "Data",
                "width": 220
            },

            {
                "fieldname": "taxable_amount",
                "label": "Taxable Amount",
                "fieldtype": "Currency",
                "width": 150
            },

            {
                "fieldname": "sub_totals",
                "label": "Sub Total",
                "fieldtype": "Currency",
                "width": 150
            },

            {
                "fieldname": "vat_payable",
                "label": "VAT Payable",
                "fieldtype": "Currency",
                "width": 150
            },

            {
                "fieldname": "mrc_number",
                "label": "MRC Number",
                "fieldtype": "Data",
                "width": 150
            },

            {
                "fieldname": "vat_recepit_number_customs_declaration_number",
                "label": "VAT Receipt No / Customs Declaration No",
                "fieldtype": "Data",
                "width": 220
            },

            {
                "fieldname": "date",
                "label": "Date",
                "fieldtype": "Date",
                "width": 120
            },

            {
                "fieldname": "phone",
                "label": "Phone",
                "fieldtype": "Data",
                "width": 140
            },

            {
                "fieldname": "remark",
                "label": "Remark",
                "fieldtype": "Data",
                "width": 180
            }

        ]


    # ========================================================
    # 15% VAT
    # ========================================================

    if report_type in [
        "15 VAT Receivable",
        "15 VAT Payable"
    ]:

        return [

            {
                "fieldname": "tax_type",
                "label": "Tax Type",
                "fieldtype": "Data",
                "width": 180
            },

            {
                "fieldname": "vat_type",
                "label": "VAT Type",
                "fieldtype": "Data",
                "width": 120
            },

            {
                "fieldname": "vat_purchase_category",
                "label": "VAT Purchase Category",
                "fieldtype": "Data",
                "width": 140
            },

            {
                "fieldname": "colander",
                "label": "Colander",
                "fieldtype": "Data",
                "width": 90
            },

            {
                "fieldname": "type_of_purchase",
                "label": "Type of Purchase",
                "fieldtype": "Data",
                "width": 110
            },

            {
                "fieldname": "tin_no",
                "label": "TIN No",
                "fieldtype": "Data",
                "width": 130
            },

            {
                "fieldname": "seller_name",
                "label": "Seller Name",
                "fieldtype": "Data",
                "width": 180
            },

            {
                "fieldname": "date_of_purchase_gc",
                "label": "Date of Purchase G.C",
                "fieldtype": "Date",
                "width": 130
            },

            {
                "fieldname": "mrc_no",
                "label": "MRC No",
                "fieldtype": "Data",
                "width": 120
            },

            {
                "fieldname": "vat_receipt_no__supplier",
                "label": "VAT Receipt No / Supplier",
                "fieldtype": "Data",
                "width": 180
            },

            {
                "fieldname": "description",
                "label": "Description",
                "fieldtype": "Data",
                "width": 180
            },

            {
                "fieldname": "unit_of_measurement",
                "label": "Unit",
                "fieldtype": "Data",
                "width": 90
            },

            {
                "fieldname": "quantity",
                "label": "Quantity",
                "fieldtype": "Float",
                "width": 100
            },

            {
                "fieldname": "unit_price",
                "label": "Unit Price",
                "fieldtype": "Currency",
                "width": 120
            },

            {
                "fieldname": "total_value_before_vat",
                "label": "Total Value Before VAT",
                "fieldtype": "Currency",
                "width": 150
            },

            {
                "fieldname": "purchase_input_or_vat_paid_on_imported_good",
                "label": "Purchase Input / VAT Paid on Imported Good",
                "fieldtype": "Currency",
                "width": 190
            },

            {
                "fieldname": "gross_input_value",
                "label": "Gross Input Value",
                "fieldtype": "Currency",
                "width": 150
            },

            {
                "fieldname": "reference_1",
                "label": "Reference 1",
                "fieldtype": "Data",
                "width": 120
            },

            {
                "fieldname": "reference_2",
                "label": "Reference 2",
                "fieldtype": "Data",
                "width": 120
            },

            {
                "fieldname": "remark",
                "label": "Remark",
                "fieldtype": "Data",
                "width": 180
            }

        ]


    # ========================================================
    # 7.5% WITHHOLDING
    # ========================================================

    if report_type == "7.5 Withholding Payable":

        return [

            {
                "fieldname": "tax_type",
                "label": "Tax Type",
                "fieldtype": "Data",
                "width": 180
            },

            {
                "fieldname": "withholdees_tin",
                "label": "Withholdees TIN",
                "fieldtype": "Data",
                "width": 140
            },

            {
                "fieldname": "withholdees_name",
                "label": "Withholdees Name",
                "fieldtype": "Data",
                "width": 180
            },

            {
                "fieldname": "taxabe_amount",
                "label": "Taxable Amount",
                "fieldtype": "Currency",
                "width": 140
            },

            {
                "fieldname": "tax_withheld",
                "label": "Tax Withheld",
                "fieldtype": "Currency",
                "width": 140
            },

            {
                "fieldname": "receipt_no",
                "label": "Receipt No",
                "fieldtype": "Data",
                "width": 130
            },

            {
                "fieldname": "receipt_date_gc",
                "label": "Receipt Date G.C",
                "fieldtype": "Date",
                "width": 130
            },

            {
                "fieldname": "reference_3",
                "label": "Reference 1",
                "fieldtype": "Data",
                "width": 120
            },

            {
                "fieldname": "reference_4",
                "label": "Reference 2",
                "fieldtype": "Data",
                "width": 120
            },

            {
                "fieldname": "remark",
                "label": "Remark",
                "fieldtype": "Data",
                "width": 180
            }

        ]


    # ========================================================
    # 3% WITHHOLDING
    # ========================================================

    if report_type in [
        "3 Withholding Payable",
        "3 Withholding Receivable"
    ]:

        return [

            {
                "fieldname": "tax_type",
                "label": "Tax Type",
                "fieldtype": "Data",
                "width": 180
            },

            {
                "fieldname": "tin_number",
                "label": "TIN Number",
                "fieldtype": "Data",
                "width": 140
            },

            {
                "fieldname": "withholders_name",
                "label": "Withholders Name",
                "fieldtype": "Data",
                "width": 180
            },

            {
                "fieldname": "receipt_nos",
                "label": "Receipt No",
                "fieldtype": "Data",
                "width": 130
            },

            {
                "fieldname": "date_in_gc",
                "label": "Date in G.C",
                "fieldtype": "Date",
                "width": 130
            },

            {
                "fieldname": "sub_total",
                "label": "Sub Total",
                "fieldtype": "Currency",
                "width": 140
            },

            {
                "fieldname": "tax_withhold",
                "label": "Tax Withhold",
                "fieldtype": "Currency",
                "width": 140
            },

            {
                "fieldname": "reference_5",
                "label": "Reference 1",
                "fieldtype": "Data",
                "width": 120
            },

            {
                "fieldname": "reference_6",
                "label": "Reference 2",
                "fieldtype": "Data",
                "width": 120
            },

            {
                "fieldname": "remark",
                "label": "Remark",
                "fieldtype": "Data",
                "width": 180
            }

        ]


    # ========================================================
    # DEFAULT
    # ========================================================

    return [

        {
            "fieldname": "tax_type",
            "label": "Tax Type",
            "fieldtype": "Data",
            "width": 200
        },

        {
            "fieldname": "remark",
            "label": "Remark",
            "fieldtype": "Data",
            "width": 200
        }

    ]


# ============================================================
# DATA
# ============================================================

def get_data(filters):

    report_type = filters.get("report_type")

    # ========================================================
    # EMPLOYEE INCOME TAX
    # ========================================================

    if report_type == "Employee Income Tax":

        conditions = []
        values = {}

        if filters.get("budget_year"):

            conditions.append(
                "ep.budget_year = %(budget_year)s"
            )

            values["budget_year"] = filters["budget_year"]

        if filters.get("budget_month"):

            conditions.append(
                "ep.budget_month = %(budget_month)s"
            )

            values["budget_month"] = filters["budget_month"]

        condition_sql = ""

        if conditions:
            condition_sql = " AND " + " AND ".join(conditions)

        return frappe.db.sql(
            f"""
            SELECT

                eps.employee_id,
                eps.employee_name,
                eps.tin_number,
                eps.date_of_joining_ec,
                eps.date_of_joining,

                IFNULL(eps.basic_salary, 0)
                    AS basic_salary,

                (
                    IFNULL(eps.taxable_transport_allowance, 0)
                    +
                    IFNULL(eps.nontaxable_transport_allowance, 0)
                ) AS transport_allowance,

                IFNULL(eps.total_non_taxable_amount, 0)
                    AS total_non_taxable_amount,

                IFNULL(eps.taxable_transport_allowance, 0)
                    AS taxable_transport_allowance,

                IFNULL(eps.overtime, 0)
                    AS overtime,

                (
                    IFNULL(eps.total_taxable_allowance, 0)
                    -
                    IFNULL(eps.overtime, 0)
                    -
                    IFNULL(eps.taxable_transport_allowance, 0)
                ) AS other_taxable_allowance,

                IFNULL(eps.total_taxable_allowance, 0)
                    AS total_taxable_allowance,

                IFNULL(eps.income_tax, 0)
                    AS income_tax,

                IFNULL(eps.cost_sharing, 0)
                    AS cost_sharing

            FROM
                `tabEmployee Payroll` ep

            INNER JOIN
                `tabEmployee Payroll Sheet` eps
                ON eps.parent = ep.name

            WHERE
                ep.docstatus = 1
                {condition_sql}

            ORDER BY
                ep.budget_year,
                ep.budget_month,
                eps.employee_name
            """,
            values,
            as_dict=True
        )


    # ========================================================
    # SALES OF BID
    # ========================================================

    if report_type == "Sales of Bid":

        conditions = []
        values = {}

        if filters.get("budget_year"):

            conditions.append(
                "trf.budget_year = %(budget_year)s"
            )

            values["budget_year"] = filters["budget_year"]

        if filters.get("budget_month"):

            conditions.append(
                "trf.budget_month = %(budget_month)s"
            )

            values["budget_month"] = filters["budget_month"]

        # Explicitly restrict to Sales of Bid
        conditions.append(
            "trfd.tax_type = 'Sales of Bid'"
        )

        condition_sql = " AND " + " AND ".join(conditions)

        return frappe.db.sql(
            f"""
            SELECT

                trfd.tin_nos,

                trfd.name1,

                trfd.descriptions,

                IFNULL(trfd.taxable_amount, 0)
                    AS taxable_amount,

                IFNULL(trfd.sub_totals, 0)
                    AS sub_totals,

                IFNULL(trfd.vat_payable, 0)
                    AS vat_payable,

                trfd.mrc_number,

                trfd.vat_recepit_number_customs_declaration_number,

                trfd.date,

                trfd.phone,

                trfd.remark

            FROM
                `tabTax Report Form` trf

            INNER JOIN
                `tabTax report Format Detail` trfd
                ON trfd.parent = trf.name

            WHERE
                trf.docstatus = 1
                {condition_sql}

            ORDER BY
                trf.budget_year,
                trf.budget_month,
                trfd.date,
                trf.creation
            """,
            values,
            as_dict=True
        )


    # ========================================================
    # EXISTING TAX REPORT
    # ========================================================

    conditions = []
    values = {}

    if filters.get("budget_year"):

        conditions.append(
            "trf.budget_year = %(budget_year)s"
        )

        values["budget_year"] = filters["budget_year"]

    if filters.get("budget_month"):

        conditions.append(
            "trf.budget_month = %(budget_month)s"
        )

        values["budget_month"] = filters["budget_month"]

    if filters.get("report_type"):

        conditions.append(
            "trfd.tax_type = %(report_type)s"
        )

        values["report_type"] = filters["report_type"]

    condition_sql = ""

    if conditions:
        condition_sql = " AND " + " AND ".join(conditions)

    return frappe.db.sql(
        f"""
        SELECT

            trfd.tax_type,

            trfd.vat_type,
            trfd.vat_purchase_category,
            trfd.colander,
            trfd.type_of_purchase,
            trfd.tin_no,
            trfd.seller_name,
            trfd.date_of_purchase_gc,
            trfd.mrc_no,
            trfd.vat_receipt_no__supplier,
            trfd.description,
            trfd.unit_of_measurement,
            trfd.quantity,
            trfd.unit_price,
            trfd.total_value_before_vat,
            trfd.purchase_input_or_vat_paid_on_imported_good,
            trfd.gross_input_value,

            trfd.withholdees_tin,
            trfd.withholdees_name,
            trfd.taxabe_amount,
            trfd.tax_withheld,
            trfd.receipt_no,
            trfd.receipt_date_gc,

            trfd.reference_1,
            trfd.reference_2,

            trfd.tin_number,
            trfd.withholders_name,
            trfd.receipt_nos,
            trfd.date_in_gc,
            trfd.sub_total,
            trfd.tax_withhold,

            trfd.reference_3,
            trfd.reference_4,
            trfd.reference_5,
            trfd.reference_6,

            trfd.remark

        FROM
            `tabTax Report Form` trf

        INNER JOIN
            `tabTax report Format Detail` trfd
            ON trfd.parent = trf.name

        WHERE
            trf.docstatus = 1
            {condition_sql}

        ORDER BY
            trf.budget_year,
            trf.budget_month,
            trf.creation
        """,
        values,
        as_dict=True
    )


# ============================================================
# CHART
# ============================================================

def get_chart_data(filters=None):

    filters = filters or {}

    report_type = filters.get("report_type")


    # ========================================================
    # EMPLOYEE INCOME TAX
    # ========================================================

    if report_type == "Employee Income Tax":

        conditions = []
        values = {}

        if filters.get("budget_year"):

            conditions.append(
                "ep.budget_year = %(budget_year)s"
            )

            values["budget_year"] = filters["budget_year"]

        if filters.get("budget_month"):

            conditions.append(
                "ep.budget_month = %(budget_month)s"
            )

            values["budget_month"] = filters["budget_month"]

        condition_sql = ""

        if conditions:
            condition_sql = " AND " + " AND ".join(conditions)

        rows = frappe.db.sql(
            f"""
            SELECT

                eps.employee_name,

                SUM(
                    IFNULL(eps.income_tax, 0)
                ) AS income_tax

            FROM
                `tabEmployee Payroll` ep

            INNER JOIN
                `tabEmployee Payroll Sheet` eps
                ON eps.parent = ep.name

            WHERE
                ep.docstatus = 1
                {condition_sql}

            GROUP BY
                eps.employee_name

            ORDER BY
                income_tax DESC

            LIMIT 20
            """,
            values,
            as_dict=True
        )

        return {
            "data": {
                "labels": [
                    row.employee_name for row in rows
                ],
                "datasets": [
                    {
                        "name": "Income Tax",
                        "values": [
                            float(row.income_tax or 0)
                            for row in rows
                        ]
                    }
                ]
            },
            "type": "bar",
            "height": 300,
            "colors": ["#2490EF"]
        }


    # ========================================================
    # SALES OF BID CHART
    # ========================================================

    if report_type == "Sales of Bid":

        conditions = []
        values = {}

        if filters.get("budget_year"):

            conditions.append(
                "trf.budget_year = %(budget_year)s"
            )

            values["budget_year"] = filters["budget_year"]

        if filters.get("budget_month"):

            conditions.append(
                "trf.budget_month = %(budget_month)s"
            )

            values["budget_month"] = filters["budget_month"]

        conditions.append(
            "trfd.tax_type = 'Sales of Bid'"
        )

        condition_sql = " AND " + " AND ".join(conditions)

        rows = frappe.db.sql(
            f"""
            SELECT

                COALESCE(
                    NULLIF(trfd.name1, ''),
                    'Unknown'
                ) AS customer_name,

                SUM(
                    IFNULL(trfd.taxable_amount, 0)
                ) AS taxable_amount,

                SUM(
                    IFNULL(trfd.vat_payable, 0)
                ) AS vat_payable

            FROM
                `tabTax Report Form` trf

            INNER JOIN
                `tabTax report Format Detail` trfd
                ON trfd.parent = trf.name

            WHERE
                trf.docstatus = 1
                {condition_sql}

            GROUP BY
                trfd.name1

            ORDER BY
                taxable_amount DESC

            LIMIT 20
            """,
            values,
            as_dict=True
        )

        return {
            "data": {
                "labels": [
                    row.customer_name for row in rows
                ],
                "datasets": [

                    {
                        "name": "Taxable Amount",
                        "values": [
                            float(row.taxable_amount or 0)
                            for row in rows
                        ]
                    },

                    {
                        "name": "VAT Payable",
                        "values": [
                            float(row.vat_payable or 0)
                            for row in rows
                        ]
                    }

                ]
            },

            "type": "bar",
            "height": 300,

            "colors": [
                "#2490EF",
                "#8E44AD"
            ]
        }


    # ========================================================
    # EXISTING TAX CHART
    # ========================================================

    conditions = []
    values = {}

    if filters.get("budget_year"):

        conditions.append(
            "trf.budget_year = %(budget_year)s"
        )

        values["budget_year"] = filters["budget_year"]

    if filters.get("budget_month"):

        conditions.append(
            "trf.budget_month = %(budget_month)s"
        )

        values["budget_month"] = filters["budget_month"]

    if filters.get("report_type"):

        conditions.append(
            "trfd.tax_type = %(report_type)s"
        )

        values["report_type"] = filters["report_type"]

    condition_sql = ""

    if conditions:
        condition_sql = " AND " + " AND ".join(conditions)

    rows = frappe.db.sql(
        f"""
        SELECT

            trfd.tax_type,

            COUNT(trfd.name)
                AS transaction_count,

            SUM(
                CASE

                    WHEN trfd.tax_type IN (
                        '15 VAT Payable',
                        '15 VAT Receivable'
                    )

                    THEN IFNULL(
                        trfd.purchase_input_or_vat_paid_on_imported_good,
                        0
                    )

                    WHEN trfd.tax_type = '7.5 Withholding Payable'

                    THEN IFNULL(
                        trfd.tax_withheld,
                        0
                    )

                    WHEN trfd.tax_type IN (
                        '3 Withholding Payable',
                        '3 Withholding Receivable'
                    )

                    THEN IFNULL(
                        trfd.tax_withhold,
                        0
                    )

                    ELSE 0

                END
            ) AS tax_amount,

            SUM(
                CASE

                    WHEN trfd.tax_type IN (
                        '15 VAT Payable',
                        '15 VAT Receivable'
                    )

                    THEN IFNULL(
                        trfd.total_value_before_vat,
                        0
                    )

                    WHEN trfd.tax_type = '7.5 Withholding Payable'

                    THEN IFNULL(
                        trfd.taxabe_amount,
                        0
                    )

                    WHEN trfd.tax_type IN (
                        '3 Withholding Payable',
                        '3 Withholding Receivable'
                    )

                    THEN IFNULL(
                        trfd.sub_total,
                        0
                    )

                    ELSE 0

                END
            ) AS taxable_amount

        FROM
            `tabTax Report Form` trf

        INNER JOIN
            `tabTax report Format Detail` trfd
            ON trfd.parent = trf.name

        WHERE
            trf.docstatus = 1
            {condition_sql}

        GROUP BY
            trfd.tax_type

        ORDER BY
            trfd.tax_type
        """,
        values,
        as_dict=True
    )

    return {
        "data": {
            "labels": [
                row.tax_type for row in rows
            ],

            "datasets": [

                {
                    "name": "Tax Amount",
                    "values": [
                        float(row.tax_amount or 0)
                        for row in rows
                    ]
                },

                {
                    "name": "Taxable Amount",
                    "values": [
                        float(row.taxable_amount or 0)
                        for row in rows
                    ]
                }

            ]
        },

        "type": "bar",
        "height": 300,

        "colors": [
            "#2490EF",
            "#8E44AD"
        ]
    }


# ============================================================
# SUMMARY CARDS
# ============================================================

def get_summary(filters=None):

    filters = filters or {}

    report_type = filters.get("report_type")


    # ========================================================
    # EMPLOYEE INCOME TAX
    # ========================================================

    if report_type == "Employee Income Tax":

        conditions = []
        values = {}

        if filters.get("budget_year"):

            conditions.append(
                "ep.budget_year = %(budget_year)s"
            )

            values["budget_year"] = filters["budget_year"]

        if filters.get("budget_month"):

            conditions.append(
                "ep.budget_month = %(budget_month)s"
            )

            values["budget_month"] = filters["budget_month"]

        condition_sql = ""

        if conditions:
            condition_sql = " AND " + " AND ".join(conditions)

        result = frappe.db.sql(
            f"""
            SELECT

                COUNT(eps.name)
                    AS transaction_count,

                SUM(
                    IFNULL(eps.total_taxable_allowance, 0)
                ) AS total_taxable_allowance,

                SUM(
                    IFNULL(eps.income_tax, 0)
                ) AS total_income_tax,

                SUM(
                    IFNULL(eps.cost_sharing, 0)
                ) AS total_cost_sharing,

                SUM(
                    IFNULL(eps.basic_salary, 0)
                ) AS total_basic_salary

            FROM
                `tabEmployee Payroll` ep

            INNER JOIN
                `tabEmployee Payroll Sheet` eps
                ON eps.parent = ep.name

            WHERE
                ep.docstatus = 1
                {condition_sql}
            """,
            values,
            as_dict=True
        )

        row = result[0] if result else {}

        return [

            {
                "value": row.get("transaction_count") or 0,
                "indicator": "Blue",
                "label": "Employees",
                "datatype": "Int"
            },

            {
                "value": row.get("total_basic_salary") or 0,
                "indicator": "Orange",
                "label": "Total Basic Salary",
                "datatype": "Currency"
            },

            {
                "value": row.get("total_taxable_allowance") or 0,
                "indicator": "Orange",
                "label": "Total Taxable Allowance",
                "datatype": "Currency"
            },

            {
                "value": row.get("total_income_tax") or 0,
                "indicator": "Green",
                "label": "Total Income Tax",
                "datatype": "Currency"
            },

            {
                "value": row.get("total_cost_sharing") or 0,
                "indicator": "Purple",
                "label": "Total Cost Sharing",
                "datatype": "Currency"
            }

        ]


    # ========================================================
    # SALES OF BID SUMMARY
    # ========================================================

    if report_type == "Sales of Bid":

        conditions = []
        values = {}

        if filters.get("budget_year"):

            conditions.append(
                "trf.budget_year = %(budget_year)s"
            )

            values["budget_year"] = filters["budget_year"]

        if filters.get("budget_month"):

            conditions.append(
                "trf.budget_month = %(budget_month)s"
            )

            values["budget_month"] = filters["budget_month"]

        conditions.append(
            "trfd.tax_type = 'Sales of Bid'"
        )

        condition_sql = " AND " + " AND ".join(conditions)

        result = frappe.db.sql(
            f"""
            SELECT

                COUNT(trfd.name)
                    AS transaction_count,

                SUM(
                    IFNULL(trfd.taxable_amount, 0)
                ) AS total_taxable_amount,

                SUM(
                    IFNULL(trfd.sub_totals, 0)
                ) AS total_sub_total,

                SUM(
                    IFNULL(trfd.vat_payable, 0)
                ) AS total_vat_payable

            FROM
                `tabTax Report Form` trf

            INNER JOIN
                `tabTax report Format Detail` trfd
                ON trfd.parent = trf.name

            WHERE
                trf.docstatus = 1
                {condition_sql}
            """,
            values,
            as_dict=True
        )

        row = result[0] if result else {}

        return [

            {
                "value": row.get("transaction_count") or 0,
                "indicator": "Blue",
                "label": "Sales of Bid",
                "datatype": "Int"
            },

            {
                "value": row.get("total_taxable_amount") or 0,
                "indicator": "Orange",
                "label": "Total Taxable Amount",
                "datatype": "Currency"
            },

            {
                "value": row.get("total_sub_total") or 0,
                "indicator": "Purple",
                "label": "Total Sub Total",
                "datatype": "Currency"
            },

            {
                "value": row.get("total_vat_payable") or 0,
                "indicator": "Green",
                "label": "Total VAT Payable",
                "datatype": "Currency"
            }

        ]


    # ========================================================
    # EXISTING TAX SUMMARY
    # ========================================================

    conditions = []
    values = {}

    if filters.get("budget_year"):

        conditions.append(
            "trf.budget_year = %(budget_year)s"
        )

        values["budget_year"] = filters["budget_year"]

    if filters.get("budget_month"):

        conditions.append(
            "trf.budget_month = %(budget_month)s"
        )

        values["budget_month"] = filters["budget_month"]

    if filters.get("report_type"):

        conditions.append(
            "trfd.tax_type = %(report_type)s"
        )

        values["report_type"] = filters["report_type"]

    condition_sql = ""

    if conditions:
        condition_sql = " AND " + " AND ".join(conditions)

    result = frappe.db.sql(
        f"""
        SELECT

            COUNT(trfd.name)
                AS transaction_count,

            SUM(

                CASE

                    WHEN trfd.tax_type IN (
                        '15 VAT Payable',
                        '15 VAT Receivable'
                    )

                    THEN IFNULL(
                        trfd.purchase_input_or_vat_paid_on_imported_good,
                        0
                    )

                    WHEN trfd.tax_type = '7.5 Withholding Payable'

                    THEN IFNULL(
                        trfd.tax_withheld,
                        0
                    )

                    WHEN trfd.tax_type IN (
                        '3 Withholding Payable',
                        '3 Withholding Receivable'
                    )

                    THEN IFNULL(
                        trfd.tax_withhold,
                        0
                    )

                    ELSE 0

                END

            ) AS total_tax,

            SUM(

                CASE

                    WHEN trfd.tax_type IN (
                        '15 VAT Payable',
                        '15 VAT Receivable'
                    )

                    THEN IFNULL(
                        trfd.total_value_before_vat,
                        0
                    )

                    WHEN trfd.tax_type = '7.5 Withholding Payable'

                    THEN IFNULL(
                        trfd.taxabe_amount,
                        0
                    )

                    WHEN trfd.tax_type IN (
                        '3 Withholding Payable',
                        '3 Withholding Receivable'
                    )

                    THEN IFNULL(
                        trfd.sub_total,
                        0
                    )

                    ELSE 0

                END

            ) AS total_taxable_amount

        FROM
            `tabTax Report Form` trf

        INNER JOIN
            `tabTax report Format Detail` trfd
            ON trfd.parent = trf.name

        WHERE
            trf.docstatus = 1
            {condition_sql}
        """,
        values,
        as_dict=True
    )

    row = result[0] if result else {}

    return [

        {
            "value": row.get("transaction_count") or 0,
            "indicator": "Blue",
            "label": "Transactions",
            "datatype": "Int"
        },

        {
            "value": row.get("total_taxable_amount") or 0,
            "indicator": "Orange",
            "label": "Total Taxable Amount",
            "datatype": "Currency"
        },

        {
            "value": row.get("total_tax") or 0,
            "indicator": "Green",
            "label": "Total Tax",
            "datatype": "Currency"
        }

    ]