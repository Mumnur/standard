import frappe
from frappe import _

def execute(filters=None):
    columns = get_columns()
    data = get_data(filters)
    return columns, data


def get_columns():
    return [
        {"label": _("Employee"), "fieldname": "employee", "fieldtype": "Link", "options": "Employee"},
        {"label": _("Employee Name"), "fieldname": "employee_name", "fieldtype": "Data"},
        {"label": _("Employemet Type"), "fieldname": "employment_type", "fieldtype": "Link", "options": "Employment Type"},
        {"label": _("School"), "fieldname": "school_univ", "fieldtype": "Data"},
        {"label": _("Level"), "fieldname": "custom_education_level", "fieldtype": "Link", "options": "Education Level"},
        {"label": _("Male"), "fieldname": "male", "fieldtype": "Int"},
        {"label": _("Female"), "fieldname": "female", "fieldtype": "Int"},
        {"label": _("Total"), "fieldname": "total", "fieldtype": "Int"},
    ]


def get_data(filters):
    conditions = ""
    values = {}

    if filters.get("level"):
        conditions += " AND edu.custom_education_level = %(level)s"
        values["level"] = filters.get("level")

    if filters.get("employment_type"):
        conditions += " AND emp.employment_type = %(employment_type)s"
        values["employment_type"] = filters.get("employment_type")

    rows = frappe.db.sql(f"""
        SELECT
            emp.name AS employee,
            emp.employee_name AS employee_name,
            emp.employment_type AS employment_type,
            emp.gender,
            edu.school_univ,
            edu.custom_education_level
        FROM `tabEmployee` emp
        JOIN `tabEmployee Education` edu ON edu.parent = emp.name
        WHERE edu.custom_current_education = 1
        {conditions}
    """, values, as_dict=True)

    male = sum(1 for r in rows if r.gender == "ወንድ")
    female = sum(1 for r in rows if r.gender == "ሴት")

    rows.append({})
    rows.append({
        "employee": "TOTAL",
        "male": male,
        "female": female,
        "total": male + female
    })

    return rows
