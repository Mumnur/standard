import frappe
from frappe import _
from frappe.utils import date_diff


def execute(filters=None):
    filters = filters or {}
    columns = get_columns()
    data = get_data(filters)
    chart = get_chart(data)
    summary = get_report_summary(data)
    return columns, data, None, chart, summary


def get_columns():
    return [
        {"label": _("Employee"), "fieldname": "name", "fieldtype": "Link", "options": "Employee", "width": 110},
        {"label": _("Employee Name"), "fieldname": "employee_name", "fieldtype": "Data", "width": 160},
        {"label": _("Gender"), "fieldname": "gender", "fieldtype": "Link", "options": "Gender", "width": 90},
        {"label": _("Department"), "fieldname": "department", "fieldtype": "Link", "options": "Department", "width": 150},
        {"label": _("Designation"), "fieldname": "designation", "fieldtype": "Link", "options": "Designation", "width": 140},
        {"label": _("Branch"), "fieldname": "branch", "fieldtype": "Link", "options": "Branch", "width": 110},
        {"label": _("Company"), "fieldname": "company", "fieldtype": "Link", "options": "Company", "width": 120},
        {"label": _("Date of Joining"), "fieldname": "date_of_joining", "fieldtype": "Date", "width": 110},
        {"label": _("Relieving Date"), "fieldname": "relieving_date", "fieldtype": "Date", "width": 110},
        {"label": _("Tenure (Days)"), "fieldname": "tenure_days", "fieldtype": "Int", "width": 100},
        {"label": _("Reason for Leaving"), "fieldname": "custom_reason", "fieldtype": "Link", "options": "Reason", "width": 150},
        {"label": _("Description for Leaving"), "fieldname": "reason_for_leaving", "fieldtype": "Small Text", "width": 220},
        {"label": _("New Workplace"), "fieldname": "new_workplace", "fieldtype": "Data", "width": 130},
        {"label": _("Notice (Days)"), "fieldname": "notice_number_of_days", "fieldtype": "Int", "width": 90},
    ]


def get_data(filters):
    conditions = get_conditions(filters)

    employees = frappe.db.sql("""
        SELECT
            name, employee_name, gender, department, designation, branch, company,
            date_of_joining, relieving_date, custom_reason, reason_for_leaving,
            new_workplace, notice_number_of_days
        FROM `tabEmployee`
        WHERE status = 'Left' {conditions}
        ORDER BY relieving_date DESC
    """.format(conditions=conditions), filters, as_dict=1)

    for emp in employees:
        if emp.date_of_joining and emp.relieving_date:
            emp.tenure_days = date_diff(emp.relieving_date, emp.date_of_joining)
        else:
            emp.tenure_days = None

    return employees


def get_conditions(filters):
    conditions = []

    if filters.get("from_relieving_date"):
        conditions.append("relieving_date >= %(from_relieving_date)s")

    if filters.get("to_relieving_date"):
        conditions.append("relieving_date <= %(to_relieving_date)s")

    if filters.get("department"):
        conditions.append("department = %(department)s")

    if filters.get("designation"):
        conditions.append("designation = %(designation)s")

    if filters.get("gender"):
        conditions.append("gender = %(gender)s")

    if filters.get("branch"):
        conditions.append("branch = %(branch)s")

    if filters.get("company"):
        conditions.append("company = %(company)s")

    if filters.get("custom_reason"):
        conditions.append("custom_reason = %(custom_reason)s")

    if conditions:
        return " AND " + " AND ".join(conditions)
    return ""


def get_chart(data):
    if not data:
        return None

    reason_count = {}
    for row in data:
        reason = row.get("custom_reason") or _("Not Specified")
        reason_count[reason] = reason_count.get(reason, 0) + 1

    return {
        "data": {
            "labels": list(reason_count.keys()),
            "datasets": [{"name": _("Employees"), "values": list(reason_count.values())}]
        },
        "type": "pie",
        "height": 280
    }


def get_report_summary(data):
    if not data:
        return []

    total = len(data)
    tenures = [row.tenure_days for row in data if row.tenure_days is not None]
    avg_tenure = round(sum(tenures) / len(tenures)) if tenures else 0

    male_count = len([r for r in data if (r.gender or "").lower() == "ወንድ"])
    female_count = len([r for r in data if (r.gender or "").lower() == "ሴት"])

    return [
        {"value": total, "label": _("Total Relieved"), "indicator": "Red", "datatype": "Int"},
        {"value": avg_tenure, "label": _("Avg. Tenure (Days)"), "indicator": "Blue", "datatype": "Int"},
        {"value": male_count, "label": _("Male"), "indicator": "Green", "datatype": "Int"},
        {"value": female_count, "label": _("Female"), "indicator": "Orange", "datatype": "Int"},
    ]