# Copyright (c) 2026, ERP Solution Ethiopia PLC
# Script Report: Uniform Registration Wcc Summary
# Summarizes uniform quantities required across Uniform Registration Wcc
# documents, grouped by Uniform Type + Measurement.

import frappe
from frappe.utils import flt


def execute(filters=None):
    filters = filters or {}
    columns = get_columns()
    data = get_data(filters)
    return columns, data


def get_conditions(filters):
    conditions = ""

    if filters.get("project"):
        conditions += " AND ur.projects = %(project)s"

    if filters.get("employee"):
        conditions += " AND urt.employee = %(employee)s"

    if filters.get("budget_year"):
        conditions += " AND ur.budget_year = %(budget_year)s"

    if filters.get("gender"):
        conditions += " AND urt.gender = %(gender)s"

    if filters.get("designation"):
        conditions += " AND urt.designation = %(designation)s"

    return conditions


def get_data(filters):
    conditions = get_conditions(filters)

    query = """
        SELECT
            ur.projects AS project,
            ur.budget_year,
            urt.employee,
            urt.employee_name,
            urt.gender,
            urt.designation,
            urt.data_6 AS uniform_type,
            urt.data_7 AS measurement,
            urt.data_8 AS qty,
            urt.data_9 AS time_range
        FROM `tabUniform Registrations Wcc Detail` urt
        INNER JOIN `tabUniform Registration Wcc` ur
            ON ur.name = urt.parent
        WHERE ur.docstatus != 2 {conditions}
    """.format(conditions=conditions)

    records = frappe.db.sql(query, filters, as_dict=True)

    summary = {}

    for row in records:
        uniform_type = row.get("uniform_type")
        measurement = row.get("measurement")
        qty = flt(row.get("qty"))

        if not uniform_type or not measurement or qty <= 0:
            continue

        key = (uniform_type, measurement)

        if key not in summary:
            summary[key] = 0

        summary[key] += qty

    data = []
    for (uniform_type, measurement), total_qty in sorted(summary.items()):
        data.append({
            "uniform_type": uniform_type,
            "measurement": measurement,
            "total_qty": total_qty,
        })

    return data


def get_columns():
    return [
        {
            "label": "Uniform Type",
            "fieldname": "uniform_type",
            "fieldtype": "Link",
            "options": "Uniform Type",
            "width": 220,
        },
        {
            "label": "Measurement",
            "fieldname": "measurement",
            "fieldtype": "Link",
            "options": "Measurement",
            "width": 180,
        },
        {
            "label": "Total Qty",
            "fieldname": "total_qty",
            "fieldtype": "Float",
            "width": 120,
        },
    ]