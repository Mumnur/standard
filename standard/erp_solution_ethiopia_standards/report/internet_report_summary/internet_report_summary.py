import frappe

def execute(filters=None):
    columns = get_columns()
    data = get_data(filters)
    chart = get_chart(data, filters)
    return columns, data, None, chart

def get_columns():
    return [
        {"label": "Department", "fieldname": "department", "fieldtype": "Link", "options": "Department", "width": 180},
        {"label": "Work Place", "fieldname": "work_place", "fieldtype": "Link", "options": "Project", "width": 180},
        {"label": "Phone(s)", "fieldname": "phone", "fieldtype": "Data", "width": 220},
        {"label": "No. of Lines", "fieldname": "line_count", "fieldtype": "Int", "width": 100},
        {"label": "Total Amount", "fieldname": "total_amount", "fieldtype": "Currency", "width": 130},
    ]

def get_data(filters):
    filters = filters or {}
    conditions = ""
    if filters.get("budget_year"):
        conditions += " AND parent_doc.budget_year = %(budget_year)s"
    if filters.get("month"):
        conditions += " AND parent_doc.month = %(month)s"
    if filters.get("department"):
        conditions += " AND child.department = %(department)s"
    if filters.get("work_place"):
        conditions += " AND child.work_place = %(work_place)s"

    group_by = filters.get("group_by") or "Department"
    group_field = "child.department" if group_by == "Department" else "child.work_place"

    data = frappe.db.sql("""
        SELECT
            child.department AS department,
            child.work_place AS work_place,
            GROUP_CONCAT(DISTINCT NULLIF(TRIM(child.phone), '') SEPARATOR ', ') AS phone,
            COUNT(child.name) AS line_count,
            SUM(CAST(NULLIF(TRIM(child.amount), '') AS DECIMAL(18,2))) AS total_amount
        FROM `tabInternet Report Form Format` child
        INNER JOIN `tabInternet Report Form` parent_doc ON parent_doc.name = child.parent
        WHERE 1=1 {conditions}
        GROUP BY {group_field}
        ORDER BY total_amount DESC
    """.format(conditions=conditions, group_field=group_field), filters, as_dict=True)

    # Add a grand total row
    if data:
        grand_total = sum([(d.total_amount or 0) for d in data])
        total_lines = sum([(d.line_count or 0) for d in data])
        data.append({
            "department": "<b>Grand Total</b>" if group_by == "Department" else "",
            "work_place": "<b>Grand Total</b>" if group_by == "Work Place" else "",
            "phone": "",
            "line_count": total_lines,
            "total_amount": grand_total
        })

    return data

def get_chart(data, filters):
    if not data:
        return None

    filters = filters or {}
    group_by = filters.get("group_by") or "Department"
    key = "department" if group_by == "Department" else "work_place"

    # Exclude the grand total row from the chart
    rows = [d for d in data if d.get(key)]
    labels = [d[key] for d in rows]
    values = [d["total_amount"] or 0 for d in rows]

    return {
        "data": {
            "labels": labels,
            "datasets": [{"name": "Total Amount by {}".format(group_by), "values": values}]
        },
        "type": "bar",
        "colors": ["#5e64ff"]
    }