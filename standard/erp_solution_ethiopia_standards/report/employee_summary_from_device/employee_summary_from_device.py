import frappe
from frappe.utils import getdate, get_time
from datetime import timedelta


def execute(filters=None):
    filters = filters or {}
    columns = get_columns()
    routes = get_daily_routes()
    data = get_data(filters, routes)
    report_summary = get_report_summary(data)
    return columns, data, None, None, report_summary


def get_columns():
    return [
        {"label": "Employee ID", "fieldname": "employee_id", "fieldtype": "Data", "width": 100},
        {"label": "Employee Name", "fieldname": "employee_name", "fieldtype": "Data", "width": 150},
        {"label": "Date", "fieldname": "check_in_date", "fieldtype": "Date", "width": 95},
        {"label": "Day", "fieldname": "day_name", "fieldtype": "Data", "width": 90},
        {"label": "Check In Time", "fieldname": "check_in_time", "fieldtype": "Data", "width": 100},
        {"label": "Check Out Time", "fieldname": "check_out_time", "fieldtype": "Data", "width": 100},
        {"label": "Late (min)", "fieldname": "late_minutes", "fieldtype": "Float", "width": 90},
        {"label": "Early Exit (min)", "fieldname": "early_exit_minutes", "fieldtype": "Float", "width": 110},
        {"label": "Leave Application", "fieldname": "leave_application", "fieldtype": "Link",
         "options": "Leave Application", "width": 150},
        {"label": "Leave Type", "fieldname": "leave_type", "fieldtype": "Data", "width": 110},
    ]


def get_daily_routes():
    """Build {day_of_week: row} from the Attendance Control doc's Daily Routes child table."""
    routes = {}
    parent = frappe.db.get_value("Attendance Control", {}, "name")
    if not parent:
        return routes

    rows = frappe.get_all(
        "Child table",
        filters={"parent": parent, "parenttype": "Attendance Control"},
        fields=["day_of_week", "strat_time", "end_time", "late_cutoff", "early_exist", "break_start", "break_end"],
    )
    for r in rows:
        routes[r.day_of_week] = r
    return routes


def time_to_minutes(value):
    """Convert a Frappe Time field value (timedelta/str/None) to minutes since midnight."""
    if not value:
        return None
    if isinstance(value, timedelta):
        return value.total_seconds() / 60
    t = get_time(value)
    return t.hour * 60 + t.minute + t.second / 60


def get_data(filters, routes):
    conditions = ["1=1"]
    values = {}

    if filters.get("employee"):
        conditions.append("employee = %(employee)s")
        values["employee"] = filters["employee"]

    if filters.get("from_date"):
        conditions.append("custom_check_in_date >= %(from_date)s")
        values["from_date"] = filters["from_date"]

    if filters.get("to_date"):
        conditions.append("custom_check_in_date <= %(to_date)s")
        values["to_date"] = filters["to_date"]

    checkins = frappe.db.sql(f"""
        SELECT
            employee, employee_id, employee_name,
            custom_check_in_date AS check_in_date,
            custom_check_in_times AS check_in_time
        FROM `tabEmployee Checkins`
        WHERE {' AND '.join(conditions)}
        ORDER BY employee_name, custom_check_in_date, custom_check_in_times
    """, values, as_dict=True)

    if not checkins:
        return []

    # Collapse each employee's raw device scans for a day into one row:
    # earliest scan = check-in, latest scan = check-out.
    grouped = {}
    for row in checkins:
        key = (row.employee, row.check_in_date)
        g = grouped.get(key)
        if not g:
            grouped[key] = {
                "employee": row.employee,
                "employee_id": row.employee_id,
                "employee_name": row.employee_name,
                "check_in_date": row.check_in_date,
                "check_in_time": row.check_in_time,
                "check_out_time": row.check_in_time,
            }
        else:
            if row.check_in_time < g["check_in_time"]:
                g["check_in_time"] = row.check_in_time
            if row.check_in_time > g["check_out_time"]:
                g["check_out_time"] = row.check_in_time

    employees = list({d.employee for d in checkins if d.employee})

    leave_conditions = ["docstatus = 1", "employee IN %(employees)s"]
    leave_values = {"employees": employees}
    if filters.get("from_date"):
        leave_conditions.append("to_date >= %(from_date)s")
        leave_values["from_date"] = filters["from_date"]
    if filters.get("to_date"):
        leave_conditions.append("from_date <= %(to_date)s")
        leave_values["to_date"] = filters["to_date"]

    leaves = frappe.db.sql(f"""
        SELECT name, employee, from_date, to_date, leave_type
        FROM `tabLeave Application`
        WHERE {' AND '.join(leave_conditions)}
    """, leave_values, as_dict=True) if employees else []

    leave_map = {}
    for lv in leaves:
        d = getdate(lv.from_date)
        end = getdate(lv.to_date)
        while d <= end:
            leave_map[(lv.employee, d)] = lv
            d = frappe.utils.add_days(d, 1)

    result = []
    for (employee, check_date_raw), g in grouped.items():
        check_date = getdate(check_date_raw) if check_date_raw else None
        day_name = check_date.strftime("%A") if check_date else ""
        route = routes.get(day_name)

        late_minutes = 0
        early_exit_minutes = 0

        if route:
            in_minutes = time_to_minutes(g["check_in_time"])
            out_minutes = time_to_minutes(g["check_out_time"])
            late_cutoff = time_to_minutes(route.late_cutoff)
            early_cutoff = time_to_minutes(route.early_exist)

            if in_minutes is not None and late_cutoff is not None and in_minutes > late_cutoff:
                late_minutes = round(in_minutes - late_cutoff, 1)

            if out_minutes is not None and early_cutoff is not None and out_minutes < early_cutoff:
                early_exit_minutes = round(early_cutoff - out_minutes, 1)

        leave = leave_map.get((employee, check_date)) if check_date else None

        result.append({
            "employee_id": g["employee_id"],
            "employee_name": g["employee_name"],
            "check_in_date": g["check_in_date"],
            "day_name": day_name,
            "check_in_time": g["check_in_time"],
            "check_out_time": g["check_out_time"],
            "late_minutes": late_minutes,
            "early_exit_minutes": early_exit_minutes,
            "leave_application": leave.name if leave else "",
            "leave_type": leave.leave_type if leave else "",
        })

    result.sort(key=lambda r: (r["employee_name"], r["check_in_date"]))
    return result


def get_report_summary(data):
    total_late = sum(r["late_minutes"] for r in data)
    total_early = sum(r["early_exit_minutes"] for r in data)
    late_count = len([r for r in data if r["late_minutes"] > 0])
    early_count = len([r for r in data if r["early_exit_minutes"] > 0])
    leave_count = len([r for r in data if r["leave_application"]])

    return [
        {"label": "Total Records", "value": len(data), "indicator": "Blue"},
        {"label": "Late Arrivals", "value": late_count, "indicator": "Orange"},
        {"label": "Early Exits", "value": early_count, "indicator": "Orange"},
        {"label": "Total Late Minutes", "value": round(total_late, 1), "indicator": "Red" if total_late else "Green"},
        {"label": "Total Early Exit Minutes", "value": round(total_early, 1), "indicator": "Red" if total_early else "Green"},
        {"label": "On Leave", "value": leave_count, "indicator": "Blue"},
    ]