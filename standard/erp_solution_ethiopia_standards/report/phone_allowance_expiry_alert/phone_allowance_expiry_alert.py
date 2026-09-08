import frappe
from frappe.utils import getdate, date_diff, nowdate

def execute(filters=None):
    columns = get_columns()
    data = get_data(filters)
    return columns, data

def get_columns():
    return [
        {"label": "Employee", "fieldname": "employee_id", "fieldtype": "Link", "options": "Employee", "width": 150},
        {"label": "Employee Name", "fieldname": "employee_name", "fieldtype": "Data", "width": 160},
        {"label": "Designation", "fieldname": "designation", "fieldtype": "Link", "options": "Designation", "width": 130},
        {"label": "Department", "fieldname": "department", "fieldtype": "Link", "options": "Department", "width": 130},
        {"label": "Budget Year", "fieldname": "budget_year", "fieldtype": "Data", "width": 100},
        {"label": "Package", "fieldname": "package", "fieldtype": "Data", "width": 100},
        {"label": "SIM Issue Date", "fieldname": "date_of_sim_issue", "fieldtype": "Date", "width": 110},
        {"label": "End Date", "fieldname": "end_date_gc", "fieldtype": "Date", "width": 110},
        {"label": "Days Remaining", "fieldname": "days_remaining", "fieldtype": "Int", "width": 120},
        {"label": "Status", "fieldname": "status", "fieldtype": "HTML", "width": 140},
    ]

def get_data(filters):
    filters = filters or {}
    conditions = ""
    if filters.get("budget_year"):
        conditions += " AND parent_doc.budget_year = %(budget_year)s"
    if filters.get("department"):
        conditions += " AND child.department = %(department)s"

    records = frappe.db.sql("""
        SELECT
            child.employee_id,
            child.designation,
            child.department,
            child.budget_year,
            child.package,
            child.date_of_sim_issue,
            child.end_date_gc
        FROM `tabPhone Allowance Child Table` child
        INNER JOIN `tabPhone Allowances` parent_doc ON parent_doc.name = child.parent
        WHERE 1=1 {conditions}
        ORDER BY child.end_date_gc ASC
    """.format(conditions=conditions), filters, as_dict=True)

    today = getdate(nowdate())
    data = []
    for row in records:
        row["employee_name"] = frappe.db.get_value("Employee", row.employee_id, "employee_name")

        if row.end_date_gc:
            end_date = getdate(row.end_date_gc)
            days_remaining = date_diff(end_date, today)
            row["days_remaining"] = days_remaining

            if days_remaining < 0:
                row["status"] = (
                    "<span style='color:white;background-color:#e03e2d;"
                    "padding:2px 10px;border-radius:10px;'>Expired</span>"
                )
            elif days_remaining <= 30:
                row["status"] = (
                    "<span style='color:white;background-color:#f39c12;"
                    "padding:2px 10px;border-radius:10px;'>Expiring Soon</span>"
                )
            else:
                row["status"] = (
                    "<span style='color:white;background-color:#28a745;"
                    "padding:2px 10px;border-radius:10px;'>Active</span>"
                )
        else:
            row["days_remaining"] = None
            row["status"] = (
                "<span style='color:white;background-color:#888;"
                "padding:2px 10px;border-radius:10px;'>No End Date</span>"
            )

        data.append(row)

    return data