import frappe

def execute(filters=None):
    filters = filters or {}
    view = filters.get("view") or "Detail"

    if view == "Detail":
        columns = get_detail_columns()
        data = get_detail_data(filters)
        return columns, data, None, None
    else:
        columns = get_summary_columns(filters)
        data = get_summary_data(filters)
        chart = get_chart(data, filters)
        return columns, data, None, chart


# ---------------- DETAIL VIEW ----------------

def get_detail_columns():
    return [
        {"label": "Document", "fieldname": "document", "fieldtype": "Link", "options": "Employee Medical Form", "width": 160},
        {"label": "Employee", "fieldname": "employee_id", "fieldtype": "Link", "options": "Employee", "width": 130},
        {"label": "Employee Name", "fieldname": "employee_name", "fieldtype": "Data", "width": 150},
        {"label": "Designation", "fieldname": "designation", "fieldtype": "Link", "options": "Designation", "width": 130},
        {"label": "Project", "fieldname": "project", "fieldtype": "Link", "options": "Project", "width": 130},
        {"label": "Budget Year", "fieldname": "budget_year", "fieldtype": "Link", "options": "Budget Year", "width": 100},
        {"label": "Date", "fieldname": "date", "fieldtype": "Date", "width": 100},
        {"label": "Reason", "fieldname": "reason", "fieldtype": "Data", "width": 180},
        {"label": "Facility Type", "fieldname": "facility_type", "fieldtype": "Data", "width": 110},
        {"label": "Amount Requested", "fieldname": "amount_paid", "fieldtype": "Float", "width": 130},
        {"label": "Amount Paid", "fieldname": "amount", "fieldtype": "Float", "width": 120},
        {"label": "Insurance Covered", "fieldname": "insu", "fieldtype": "Currency", "width": 140},
    ]

def get_detail_data(filters):
    conditions = build_conditions(filters)

    rows = frappe.db.sql("""
        SELECT
            parent_doc.name AS document,
            parent_doc.employee_id AS employee_id,
            parent_doc.designation AS designation,
            parent_doc.project AS project,
            parent_doc.budget_year AS budget_year,
            parent_doc.date AS date,
            child.reason AS reason,
            child.data_3 AS facility_type,
            child.amount_paid AS amount_paid,
            child.amount AS amount,
            child.insu AS insu
        FROM `tabMedical Form` child
        INNER JOIN `tabEmployee Medical Form` parent_doc ON parent_doc.name = child.parent
        WHERE 1=1 {conditions}
        ORDER BY parent_doc.date DESC
    """.format(conditions=conditions), filters, as_dict=True)

    # Employee Name is not a field on Employee Medical Form, so fetch it
    # live from the Employee master (cached per employee to avoid repeat queries)
    employee_name_cache = {}
    for row in rows:
        emp = row.get("employee_id")
        if emp:
            if emp not in employee_name_cache:
                employee_name_cache[emp] = frappe.db.get_value("Employee", emp, "employee_name")
            row["employee_name"] = employee_name_cache[emp]
        else:
            row["employee_name"] = None

    return rows


# ---------------- SUMMARY VIEW ----------------

GROUP_MAP = {
    "Reason": ("child.reason", "reason", "Reason", "Select"),
    "Project": ("parent_doc.project", "project", "Project", "Link"),
    "Budget Year": ("parent_doc.budget_year", "budget_year", "Budget Year", "Link"),
    "Type of Employee": ("parent_doc.type_of_employee", "type_of_employee", "Type of Employee", "Select"),
    "Injury Type": ("parent_doc.injury_type", "injury_type", "Injury Type", "Select"),
    "Facility Type": ("child.data_3", "facility_type", "Facility Type", "Select"),
}

def get_summary_columns(filters):
    group_by = filters.get("group_by") or "Reason"
    _, fieldname, label, fieldtype = GROUP_MAP[group_by]

    col = {"label": label, "fieldname": fieldname, "fieldtype": fieldtype, "width": 200}
    if fieldtype == "Link":
        col["options"] = "Project" if group_by == "Project" else "Budget Year"

    return [
        col,
        {"label": "No. of Records", "fieldname": "record_count", "fieldtype": "Int", "width": 110},
        {"label": "Amount Requested", "fieldname": "total_amount_paid", "fieldtype": "Float", "width": 140},
        {"label": "Amount Paid", "fieldname": "total_amount", "fieldtype": "Float", "width": 130},
        {"label": "Insurance Covered", "fieldname": "total_insu", "fieldtype": "Currency", "width": 140},
        {"label": "Avg %", "fieldname": "avg_percent", "fieldtype": "Float", "width": 90},
    ]

def get_summary_data(filters):
    group_by = filters.get("group_by") or "Reason"
    group_field, group_alias, _, _ = GROUP_MAP[group_by]
    conditions = build_conditions(filters)

    data = frappe.db.sql("""
        SELECT
            {group_field} AS {group_alias},
            COUNT(child.name) AS record_count,
            SUM(child.amount_paid) AS total_amount_paid,
            SUM(child.amount) AS total_amount,
            SUM(child.insu) AS total_insu,
            AVG(child.percent) AS avg_percent
        FROM `tabMedical Form` child
        INNER JOIN `tabEmployee Medical Form` parent_doc ON parent_doc.name = child.parent
        WHERE 1=1 {conditions}
        GROUP BY {group_field}
        ORDER BY total_amount DESC
    """.format(group_field=group_field, group_alias=group_alias, conditions=conditions),
        filters, as_dict=True)

    if data:
        data.append({
            group_alias: "<b>Grand Total</b>",
            "record_count": sum([(d.record_count or 0) for d in data]),
            "total_amount_paid": sum([(d.total_amount_paid or 0) for d in data]),
            "total_amount": sum([(d.total_amount or 0) for d in data]),
            "total_insu": sum([(d.total_insu or 0) for d in data]),
            "avg_percent": None
        })

    return data

def get_chart(data, filters):
    if not data:
        return None
    group_by = filters.get("group_by") or "Reason"
    _, group_alias, _, _ = GROUP_MAP[group_by]

    rows = [d for d in data if d.get(group_alias) and d.get(group_alias) != "<b>Grand Total</b>"]
    labels = [d[group_alias] for d in rows]
    values = [d["total_amount"] or 0 for d in rows]

    return {
        "data": {"labels": labels, "datasets": [{"name": "Amount Paid by {}".format(group_by), "values": values}]},
        "type": "bar",
        "colors": ["#e03e2d"]
    }


# ---------------- SHARED ----------------

def build_conditions(filters):
    conditions = ""
    if filters.get("from_date"):
        conditions += " AND parent_doc.date >= %(from_date)s"
    if filters.get("to_date"):
        conditions += " AND parent_doc.date <= %(to_date)s"
    if filters.get("project"):
        conditions += " AND parent_doc.project = %(project)s"
    if filters.get("budget_year"):
        conditions += " AND parent_doc.budget_year = %(budget_year)s"
    if filters.get("employee_id"):
        conditions += " AND parent_doc.employee_id = %(employee_id)s"
    if filters.get("gender"):
        conditions += " AND parent_doc.gender = %(gender)s"
    if filters.get("type_of_injury"):
        conditions += " AND parent_doc.type_of_injury = %(type_of_injury)s"
    if filters.get("type_of_employee"):
        conditions += " AND parent_doc.type_of_employee = %(type_of_employee)s"
    if filters.get("injury_type"):
        conditions += " AND parent_doc.injury_type = %(injury_type)s"
    if filters.get("reason"):
        conditions += " AND child.reason = %(reason)s"
    if filters.get("facility_type"):
        conditions += " AND child.data_3 = %(facility_type)s"
    return conditions