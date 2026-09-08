# # -*- coding: utf-8 -*-
# from __future__ import unicode_literals
# import frappe
# from frappe.utils import flt

# def execute(filters=None):
#     if not filters:
#         filters = {}

#     columns = get_columns()
#     data = []

#     conditions = ""
#     if filters.get("project"):
#         conditions += " AND ur.projects = %(project)s"
#     if filters.get("employee_id"):
#         conditions += " AND urt.employee_id = %(employee_id)s"
#     if filters.get("budget_year"):
#         conditions += " AND ur.budget_year = %(budget_year)s"

#     # Define fields
#     type_fields = ["data_6", "data_10", "data_15", "data_20", "data_25", "data_30", "data_35", "data_40", "data_45", "data_50","data_54","data_57","data_60"]
#     measurement_fields = ["data_7", "data_11", "data_16", "data_21", "data_26", "data_31", "data_35", "data_41", "data_46", "data_51","data_55","data_58","data_61"]
#     qty_fields = ["data_8", "data_12", "data_17", "data_22", "data_27", "data_32", "data_36", "data_42", "data_47", "data_52","data_56","data_59","data_62"]

#     query = """
#         SELECT urt.employee_id, ur.projects, ur.budget_year,
#                {fields}
#         FROM `tabUniform Registration Type` urt
#         LEFT JOIN `tabUniform Registrations` ur ON ur.name = urt.parent
#         WHERE ur.docstatus != 2 {conditions}
#     """.format(
#         fields=", ".join(["urt.`{}`".format(f) for f in type_fields + measurement_fields + qty_fields]),
#         conditions=conditions
#     )

#     records = frappe.db.sql(query, filters, as_dict=1)

#     summary = {}

#     for row in records:
#         for i in range(len(type_fields)):
#             uniform_type = row.get(type_fields[i])
#             measurement = row.get(measurement_fields[i])
#             qty = flt(row.get(qty_fields[i]))

#             if not uniform_type or not measurement or not qty:
#                 continue

#             key = (uniform_type, measurement)

#             if key not in summary:
#                 summary[key] = 0.0
#             summary[key] += qty

#     for key in summary:
#         uniform_type, measurement = key
#         data.append([uniform_type, measurement, summary[key]])

#     return columns, data


# def get_columns():
#     return [
#         {
#             "label": "Uniform Type",
#             "fieldname": "uniform_type",
#             "fieldtype": "Link",
#             "options": "Uniform Type",
#             "width": 200
#         },
#         {
#             "label": "Measurement",
#             "fieldname": "measurement",
#             "fieldtype": "Link",
#             "options": "Measurement",
#             "width": 150
#         },
#         {
#             "label": "Total Qty",
#             "fieldname": "total_qty",
#             "fieldtype": "Float",
#             "width": 120
#         }
#     ]
# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import frappe
from frappe.utils import flt


def execute(filters=None):
    if not filters:
        filters = {}

    columns = get_columns()
    data = []

    conditions = ""

    if filters.get("project"):
        conditions += " AND ur.projects = %(project)s"

    if filters.get("employee_id"):
        conditions += " AND urt.employee_id = %(employee_id)s"

    if filters.get("budget_year"):
        conditions += " AND ur.budget_year = %(budget_year)s"

    # Uniform Type fields
    type_fields = [
        "data_6",
        "data_10",
        "data_15",
        "data_20",
        "data_25",
        "data_30",
        "data_35",
        "data_40",
        "data_45",
        "data_50",
        "data_54",
        "data_57",
        "data_60"
    ]

    # Measurement fields
    measurement_fields = [
        "data_7",
        "data_11",
        "data_16",
        "data_21",
        "data_26",
        "data_31",
        "data_36",
        "data_41",
        "data_46",
        "data_51",
        "data_55",
        "data_58",
        "data_61"
    ]

    # Quantity fields
    qty_fields = [
        "data_8",
        "data_12",
        "data_17",
        "data_22",
        "data_27",
        "data_32",
        "data_37",
        "data_42",
        "data_47",
        "data_52",
        "data_56",
        "data_59",
        "data_62"
    ]

    query = """
        SELECT
            ur.projects,
            ur.budget_year,
            urt.employee_id,
            {fields}
        FROM `tabUniform Registration Type` urt
        INNER JOIN `tabUniform Registrations` ur
            ON ur.name = urt.parent
        WHERE ur.docstatus != 2
        {conditions}
    """.format(
        fields=", ".join(
            ["urt.`{}`".format(f) for f in (type_fields + measurement_fields + qty_fields)]
        ),
        conditions=conditions
    )

    records = frappe.db.sql(query, filters, as_dict=True)

    summary = {}

    for row in records:
        for i in range(len(type_fields)):

            uniform_type = row.get(type_fields[i])
            measurement = row.get(measurement_fields[i])
            qty = flt(row.get(qty_fields[i]))

            if not uniform_type or not measurement or qty <= 0:
                continue

            key = (uniform_type, measurement)

            if key not in summary:
                summary[key] = 0

            summary[key] += qty

    for (uniform_type, measurement), total_qty in sorted(summary.items()):
        data.append({
            "uniform_type": uniform_type,
            "measurement": measurement,
            "total_qty": total_qty
        })

    return columns, data


def get_columns():
    return [
        {
            "label": "Uniform Type",
            "fieldname": "uniform_type",
            "fieldtype": "Link",
            "options": "Uniform Type",
            "width": 220
        },
        {
            "label": "Measurement",
            "fieldname": "measurement",
            "fieldtype": "Link",
            "options": "Measurement",
            "width": 180
        },
        {
            "label": "Total Qty",
            "fieldname": "total_qty",
            "fieldtype": "Float",
            "width": 120
        }
    ]