import frappe

def execute(filters=None):
    columns = get_columns()
    data = get_data(filters)
    chart = get_chart(data)
    return columns, data, None, chart

def get_columns():
    return [
        {"label": "Document", "fieldname": "document", "fieldtype": "Link", "options": "Milk Allowance Payment Form", "width": 150},
        {"label": "Budget Year", "fieldname": "budget_year", "fieldtype": "Link", "options": "Budget Year", "width": 100},
        {"label": "Month", "fieldname": "month", "fieldtype": "Link", "options": "Budget Month", "width": 110},
        {"label": "Employee", "fieldname": "employee_id", "fieldtype": "Link", "options": "Employee", "width": 120},
        {"label": "Employee Name", "fieldname": "employee_full_name", "fieldtype": "Data", "width": 150},
        {"label": "Employee Old Id", "fieldname": "employee_old_id", "fieldtype": "Data", "width": 110},
        {"label": "Designation", "fieldname": "designation", "fieldtype": "Link", "options": "Designation", "width": 130},
        {"label": "Department", "fieldname": "department", "fieldtype": "Link", "options": "Department", "width": 130},
        {"label": "Quantity/Month", "fieldname": "quantity_of_milk_per_month", "fieldtype": "Float", "width": 110},
        {"label": "Price One", "fieldname": "price_one", "fieldtype": "Currency", "width": 100},
        {"label": "Total Price", "fieldname": "total_price", "fieldtype": "Currency", "width": 110},
    ]

def get_data(filters):
    filters = filters or {}
    conditions = ""
    if filters.get("budget_year"):
        conditions += " AND parent_doc.budget_year = %(budget_year)s"
    if filters.get("month"):
        conditions += " AND parent_doc.month = %(month)s"
    if filters.get("employee_id"):
        conditions += " AND child.employee_id = %(employee_id)s"
    if filters.get("department"):
        conditions += " AND child.department = %(department)s"
    if filters.get("designation"):
        conditions += " AND child.designation = %(designation)s"

    data = frappe.db.sql("""
        SELECT
            parent_doc.name AS document,
            parent_doc.budget_year AS budget_year,
            parent_doc.month AS month,
            child.employee_id AS employee_id,
            child.employee_full_name AS employee_full_name,
            child.employee_old_id AS employee_old_id,
            child.designation AS designation,
            child.department AS department,
            child.quantity_of_milk_per_month AS quantity_of_milk_per_month,
            child.price_one AS price_one,
            child.total_price AS total_price
        FROM `tabMilk Allowance Payment Form Table` child
        INNER JOIN `tabMilk Allowance Payment Form` parent_doc ON parent_doc.name = child.parent
        WHERE 1=1 {conditions}
        ORDER BY parent_doc.budget_year DESC, parent_doc.month DESC, child.employee_full_name ASC
    """.format(conditions=conditions), filters, as_dict=True)

    if data:
        grand_total_qty = sum([(d.quantity_of_milk_per_month or 0) for d in data])
        grand_total_price = sum([(d.total_price or 0) for d in data])
        data.append({
            "document": "",
            "budget_year": "",
            "month": "",
            "employee_id": "",
            "employee_full_name": "<b>Grand Total</b>",
            "employee_old_id": "",
            "designation": "",
            "department": "",
            "quantity_of_milk_per_month": grand_total_qty,
            "price_one": None,
            "total_price": grand_total_price
        })

    return data

def get_chart(data):
    if not data:
        return None

    rows = [d for d in data if d.get("employee_full_name") and d.get("employee_full_name") != "<b>Grand Total</b>"]

    # Aggregate total price by department for the chart
    dept_totals = {}
    for d in rows:
        dept = d.get("department") or "Unassigned"
        dept_totals[dept] = dept_totals.get(dept, 0) + (d.get("total_price") or 0)

    labels = list(dept_totals.keys())
    values = list(dept_totals.values())

    return {
        "data": {
            "labels": labels,
            "datasets": [{"name": "Total Milk Allowance by Department", "values": values}]
        },
        "type": "bar",
        "colors": ["#5e64ff"]
    }