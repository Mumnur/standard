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
        {"label": _("Employee ID"), "fieldname": "custom_employee_id", "fieldtype": "Data", "width": 100},
        {"label": _("Project"), "fieldname": "custom_projects", "fieldtype": "Data", "width": 120},
        {"label": _("Leave Type"), "fieldname": "leave_type", "fieldtype": "Link",
         "options": "Leave Type", "width": 120},
        {"label": _("Department"), "fieldname": "department", "fieldtype": "Link",
         "options": "Department", "width": 130},
        {"label": _("Company"), "fieldname": "company", "fieldtype": "Link",
         "options": "Company", "width": 120},
        {"label": _("Is Half Day"), "fieldname": "is_half_day", "fieldtype": "Check", "width": 90},
        # Full leave range - always shown, regardless of is_half_day.
        {"label": _("From Date"), "fieldname": "from_date", "fieldtype": "Date", "width": 100},
        {"label": _("To Date"), "fieldname": "to_date", "fieldtype": "Date", "width": 100},
        {"label": _("From Date (EC)"), "fieldname": "custom_from_date_ec", "fieldtype": "Data", "width": 110},
        {"label": _("To Date (EC)"), "fieldname": "custom_to_date_ec", "fieldtype": "Data", "width": 110},
        # Half day range - only populated when is_half_day is checked, shown
        # alongside the full range rather than replacing it.
        {"label": _("Half Day Start"), "fieldname": "half_day_from_date", "fieldtype": "Date", "width": 100},
        {"label": _("Half Day End"), "fieldname": "half_day_to_date", "fieldtype": "Date", "width": 100},
        {"label": _("Half Day Start (EC)"), "fieldname": "custom_half_day_start_date_ec", "fieldtype": "Data", "width": 120},
        {"label": _("Half Day End (EC)"), "fieldname": "custom_half_day_to_end_date_ec", "fieldtype": "Data", "width": 120},
        {"label": _("Total Days"), "fieldname": "total_leave_days", "fieldtype": "Float", "width": 90},
        {"label": _("Status"), "fieldname": "status", "fieldtype": "Data", "width": 90},
    ]


def get_data(filters):
    conditions = get_conditions(filters)

    leave_applications = frappe.db.sql(
        """
        SELECT
            employee,
            employee_name,
            custom_employee_id,
            custom_projects,
            leave_type,
            department,
            company,
            is_half_day,
            from_date,
            to_date,
            custom_from_date_ec,
            custom_to_date_ec,
            half_day_from_date,
            half_day_to_date,
            custom_half_day_start_date_ec,
            custom_half_day_to_end_date_ec,
            total_leave_days,
            status
        FROM `tabLeave Application`
        WHERE docstatus < 2 {conditions}
        ORDER BY from_date DESC
        """.format(conditions=conditions),
        filters,
        as_dict=1,
    )

    # No overwriting: full range and half-day fields are separate columns,
    # so half-day rows naturally show both without losing the full range.
    return leave_applications


def get_conditions(filters):
    conditions = ""

    # Overlap logic: pick up any leave application whose range touches the
    # selected From Date - To Date window, not just ones fully inside it.
    if filters.get("from_date") and filters.get("to_date"):
        conditions += " AND from_date <= %(to_date)s AND to_date >= %(from_date)s"
    elif filters.get("from_date"):
        conditions += " AND to_date >= %(from_date)s"
    elif filters.get("to_date"):
        conditions += " AND from_date <= %(to_date)s"

    if filters.get("employee"):
        conditions += " AND employee = %(employee)s"

    if filters.get("custom_projects"):
        conditions += " AND custom_projects LIKE %(custom_projects)s"
        filters["custom_projects"] = "%" + filters.get("custom_projects") + "%"

    if filters.get("leave_type"):
        conditions += " AND leave_type = %(leave_type)s"

    if filters.get("company"):
        conditions += " AND company = %(company)s"

    if filters.get("department"):
        conditions += " AND department = %(department)s"

    if filters.get("is_half_day"):
        conditions += " AND is_half_day = %(is_half_day)s"

    return conditions