import frappe
from frappe import _


def execute(filters=None):
    filters = filters or {}
    columns = get_columns()
    data = get_data(filters)
    return columns, data


def get_columns():
    return [
        {"label": _("Employee"), "fieldname": "employee", "fieldtype": "Link",
         "options": "Employee", "width": 120},
        {"label": _("Employee Name"), "fieldname": "employee_name", "fieldtype": "Data", "width": 150},
        {"label": _("Employee ID"), "fieldname": "employee_id_no", "fieldtype": "Data", "width": 100},
        {"label": _("Department"), "fieldname": "department", "fieldtype": "Link",
         "options": "Department", "width": 130},
        {"label": _("Project"), "fieldname": "projects", "fieldtype": "Link",
         "options": "Project", "width": 120},
        {"label": _("ሰራተኛ/የስራ መሪ"), "fieldname": "role", "fieldtype": "Data", "width": 100},
        {"label": _("Budget Year"), "fieldname": "budget_year", "fieldtype": "Link",
         "options": "Budget Year", "width": 110},
        # --- child table: Leave Programme Table (one row per period) ---
        {"label": _("From (EC)"), "fieldname": "date_ec", "fieldtype": "Data", "width": 100},
        {"label": _("To (EC)"), "fieldname": "i_date_ec", "fieldtype": "Data", "width": 100},
        {"label": _("From Date"), "fieldname": "from_date", "fieldtype": "Date", "width": 100},
        {"label": _("To Date"), "fieldname": "to_date", "fieldtype": "Date", "width": 100},
        {"label": _("Requested Days"), "fieldname": "requested", "fieldtype": "Float", "width": 100},
        {"label": _("From Date (GC)"), "fieldname": "from_date_gc", "fieldtype": "Date", "width": 110},
        {"label": _("To Date (GC)"), "fieldname": "to_date_gc", "fieldtype": "Date", "width": 110},
        {"label": _("Given Days"), "fieldname": "given", "fieldtype": "Float", "width": 90},
        # --- parent totals, repeated on every row for reference ---
        {"label": _("Total Requested"), "fieldname": "requestedd", "fieldtype": "Float", "width": 110},
    ]


def get_data(filters):
    conditions = get_conditions(filters)

    return frappe.db.sql(
        """
        SELECT
            parent.employee,
            parent.employee_name,
            parent.employee_id_no,
            parent.department,
            parent.projects,
            parent.`ሰራተኛየስራ_መሪ` AS role,
            parent.budget_year,
            child.date_ec,
            child.i_date_ec,
            child.from_date,
            child.to_date,
            child.requested,
            child.ec_date_ec,
            child.ed_date_ec,
            child.from_date_gc,
            child.to_date_gc,
            parent.requestedd
        FROM `tabAnnual Leave Program` parent
        INNER JOIN `tabLeave Programme Table` child
            ON child.parent = parent.name AND child.parenttype = 'Annual Leave Program'
        WHERE parent.docstatus = 1 {conditions}
        ORDER BY parent.employee_name, child.idx
        """.format(conditions=conditions),
        filters,
        as_dict=1,
    )


def get_conditions(filters):
    conditions = ""

    if filters.get("department"):
        conditions += " AND parent.department = %(department)s"

    if filters.get("employee"):
        conditions += " AND parent.employee = %(employee)s"

    if filters.get("budget_year"):
        conditions += " AND parent.budget_year = %(budget_year)s"

    if filters.get("project"):
        conditions += " AND parent.projects = %(project)s"    

    # Overlap logic: pick up any leave period whose from_date-to_date range
    # touches the selected From Date - To Date window.
    if filters.get("from_date") and filters.get("to_date"):
        conditions += " AND child.from_date <= %(to_date)s AND child.to_date >= %(from_date)s"
    elif filters.get("from_date"):
        conditions += " AND child.to_date >= %(from_date)s"
    elif filters.get("to_date"):
        conditions += " AND child.from_date <= %(to_date)s"

    return conditions