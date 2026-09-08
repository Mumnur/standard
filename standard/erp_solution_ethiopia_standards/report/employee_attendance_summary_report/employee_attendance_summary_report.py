import frappe

def execute(filters=None):
    filters = filters or {}
    view = filters.get("view") or "Summary"

    if view == "Detail":
        columns = get_detail_columns()
        data = get_detail_data(filters)
        return columns, data, None, None
    else:
        columns = get_summary_columns()
        data = get_summary_data(filters)
        chart = get_chart(data)
        return columns, data, None, chart


# ---------------- DETAIL VIEW ----------------

def get_detail_columns():
    return [
        {"label": "Document", "fieldname": "document", "fieldtype": "Link", "options": "Employee Attendance", "width": 150},
        {"label": "Company Branch", "fieldname": "company_branch", "fieldtype": "Link", "options": "Company Branch", "width": 130},
        {"label": "Employment Type", "fieldname": "employment_type", "fieldtype": "Link", "options": "Employment Type", "width": 120},
        {"label": "Budget Year", "fieldname": "budget_year", "fieldtype": "Link", "options": "Budget Year", "width": 100},
        {"label": "Budget Month", "fieldname": "budget_month", "fieldtype": "Link", "options": "Budget Month", "width": 110},
        {"label": "Employee", "fieldname": "employee_id", "fieldtype": "Link", "options": "Employee", "width": 120},
        {"label": "Employee Name", "fieldname": "employee_name", "fieldtype": "Data", "width": 150},
        {"label": "Working Days", "fieldname": "working_days", "fieldtype": "Float", "width": 100},
        {"label": "Absent Days", "fieldname": "absent_days", "fieldtype": "Int", "width": 100},
        {"label": "Absent Hrs", "fieldname": "absent_hours", "fieldtype": "Int", "width": 90},
        {"label": "Absent Min", "fieldname": "absent_minutes", "fieldtype": "Int", "width": 90},
        {"label": "Absent Sec", "fieldname": "absent_seconds", "fieldtype": "Int", "width": 90},
    ]

def get_detail_data(filters):
    conditions = build_conditions(filters)

    data = frappe.db.sql("""
        SELECT
            parent_doc.name AS document,
            parent_doc.company_branch AS company_branch,
            parent_doc.employment_type AS employment_type,
            parent_doc.budget_year AS budget_year,
            parent_doc.budget_month AS budget_month,
            child.employee_id AS employee_id,
            child.employee_name AS employee_name,
            child.working_days AS working_days,
            child.absent_days AS absent_days,
            child.absent_hours AS absent_hours,
            child.absent_minutes AS absent_minutes,
            child.absent_seconds AS absent_seconds
        FROM `tabEmployee Attendance Table` child
        INNER JOIN `tabEmployee Attendance` parent_doc ON parent_doc.name = child.parent
        WHERE 1=1 {conditions}
        ORDER BY parent_doc.budget_year DESC, parent_doc.budget_month DESC, child.employee_name ASC
    """.format(conditions=conditions), filters, as_dict=True)

    if data:
        data.append({
            "document": "",
            "company_branch": "",
            "employment_type": "",
            "budget_year": "",
            "budget_month": "",
            "employee_id": "",
            "employee_name": "<b>Grand Total</b>",
            "working_days": sum([(d.working_days or 0) for d in data]),
            "absent_days": sum([(d.absent_days or 0) for d in data]),
            "absent_hours": sum([(d.absent_hours or 0) for d in data]),
            "absent_minutes": sum([(d.absent_minutes or 0) for d in data]),
            "absent_seconds": sum([(d.absent_seconds or 0) for d in data]),
        })

    return data


# ---------------- SUMMARY VIEW (grouped/summed per employee) ----------------

def get_summary_columns():
    return [
        {"label": "Employee", "fieldname": "employee_id", "fieldtype": "Link", "options": "Employee", "width": 120},
        {"label": "Employee Name", "fieldname": "employee_name", "fieldtype": "Data", "width": 160},
        {"label": "No. of Records", "fieldname": "record_count", "fieldtype": "Int", "width": 110},
        {"label": "Total Working Days", "fieldname": "total_working_days", "fieldtype": "Float", "width": 140},
        {"label": "Total Absent Days", "fieldname": "total_absent_days", "fieldtype": "Int", "width": 130},
        {"label": "Total Absent Hrs", "fieldname": "total_absent_hours", "fieldtype": "Int", "width": 120},
        {"label": "Total Absent Min", "fieldname": "total_absent_minutes", "fieldtype": "Int", "width": 120},
        {"label": "Total Absent Sec", "fieldname": "total_absent_seconds", "fieldtype": "Int", "width": 120},
    ]

def get_summary_data(filters):
    conditions = build_conditions(filters)

    data = frappe.db.sql("""
        SELECT
            child.employee_id AS employee_id,
            child.employee_name AS employee_name,
            COUNT(child.name) AS record_count,
            SUM(child.working_days) AS total_working_days,
            SUM(child.absent_days) AS total_absent_days,
            SUM(child.absent_hours) AS total_absent_hours,
            SUM(child.absent_minutes) AS total_absent_minutes,
            SUM(child.absent_seconds) AS total_absent_seconds
        FROM `tabEmployee Attendance Table` child
        INNER JOIN `tabEmployee Attendance` parent_doc ON parent_doc.name = child.parent
        WHERE 1=1 {conditions}
        GROUP BY child.employee_id, child.employee_name
        ORDER BY total_working_days DESC
    """.format(conditions=conditions), filters, as_dict=True)

    if data:
        data.append({
            "employee_id": "",
            "employee_name": "<b>Grand Total</b>",
            "record_count": sum([(d.record_count or 0) for d in data]),
            "total_working_days": sum([(d.total_working_days or 0) for d in data]),
            "total_absent_days": sum([(d.total_absent_days or 0) for d in data]),
            "total_absent_hours": sum([(d.total_absent_hours or 0) for d in data]),
            "total_absent_minutes": sum([(d.total_absent_minutes or 0) for d in data]),
            "total_absent_seconds": sum([(d.total_absent_seconds or 0) for d in data]),
        })

    return data

def get_chart(data):
    if not data:
        return None
    rows = [d for d in data if d.get("employee_name") and d.get("employee_name") != "<b>Grand Total</b>"]
    labels = [d["employee_name"] for d in rows]
    values = [d["total_working_days"] or 0 for d in rows]

    return {
        "data": {
            "labels": labels,
            "datasets": [{"name": "Total Working Days", "values": values}]
        },
        "type": "bar",
        "colors": ["#28a745"]
    }


# ---------------- SHARED ----------------

def build_conditions(filters):
    conditions = ""
    if filters.get("company_branch"):
        conditions += " AND parent_doc.company_branch = %(company_branch)s"
    if filters.get("employment_type"):
        conditions += " AND parent_doc.employment_type = %(employment_type)s"
    if filters.get("budget_year"):
        conditions += " AND parent_doc.budget_year = %(budget_year)s"
    if filters.get("budget_month"):
        conditions += " AND parent_doc.budget_month = %(budget_month)s"
    if filters.get("employee_id"):
        conditions += " AND child.employee_id = %(employee_id)s"
    return conditions