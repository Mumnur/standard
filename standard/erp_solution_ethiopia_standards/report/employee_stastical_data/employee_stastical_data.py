import frappe
from frappe.utils import date_diff, nowdate, today, getdate

def execute(filters=None):
    if filters and filters.get("salary_ranges"):
        filters["salary_ranges"] = parse_salary_ranges(filters.get("salary_ranges"))

    columns = get_columns()
    data = []

    data += salary_statistics(filters)
    data.append({})
    data += education_statistics(filters)
    data.append({})
    data += manpower_statistics(filters)
    data.append({})
    data += experience_statistics(filters)
    data.append({})
    data += age_statistics(filters)
    data.append({})
    data += department_statistics(filters)
    data.append({})
    data += designation_statistics(filters)

    return columns, data


# ----------------------------------
# Columns
# ----------------------------------
def get_columns():
    return [
        {"label": "Category", "fieldname": "category", "fieldtype": "Data", "width": 260},
        {"label": "Male", "fieldname": "male", "fieldtype": "Int", "width": 100},
        {"label": "Female", "fieldname": "female", "fieldtype": "Int", "width": 100},
        {"label": "Total", "fieldname": "total", "fieldtype": "Int", "width": 100},
    ]


# ----------------------------------
# Common Filter Builder
# ----------------------------------
def get_employee_filters(filters):
    emp_filters = {}

    if filters:
        if filters.get("status") and filters["status"] != "All":
            emp_filters["status"] = filters["status"]

        if filters.get("employment_type"):
            emp_filters["employment_type"] = filters["employment_type"]

    return emp_filters


# ----------------------------------
# Helper
# FIX: keys must match column fieldnames ("male"/"female"), not the
# Amharic literals. The Amharic strings are only used to compare the
# *value* stored in Employee.gender, not as dict keys.
# ----------------------------------
def mf_count(rows):
    m = sum(1 for r in rows if r.gender == "ወንድ")
    f = sum(1 for r in rows if r.gender == "ሴት")
    return m, f, m + f


def row(category, m, f, t, **kwargs):
    """Builds a report row with keys matching the column fieldnames."""
    d = {"category": category, "male": m, "female": f, "total": t}
    d.update(kwargs)
    return d


# ----------------------------------
# Salary Statistics
# ----------------------------------
def parse_salary_ranges(filter_value):
    ranges = []
    if not filter_value:
        return None
    for part in filter_value.split(","):
        parts = part.strip().split("-")
        try:
            if len(parts) == 2:
                ranges.append((int(parts[0]), int(parts[1])))
            elif len(parts) == 1:
                ranges.append((int(parts[0]), None))
        except ValueError:
            continue
    return ranges


def salary_statistics(filters=None):
    data = []
    data.append({"category": "Employees Statistical Data In Salary", "is_group": 1})

    total_m = total_f = total_t = 0

    default_ranges = [
        (1500, 1838),
        (1839, 2758),
        (2759, 4050),
        (4051, 7072),
        (7073, 10685),
        (10686, 14009),
        (14010, None),
    ]

    salary_ranges = filters.get("salary_ranges") if filters else None
    ranges = salary_ranges if salary_ranges else default_ranges

    employees = frappe.get_all(
        "Employee",
        fields=["gender", "custom_basic_salary"],
        filters=get_employee_filters(filters),
    )

    for r in ranges:
        min_sal, max_sal = r
        label = f"From birr {min_sal} – {max_sal}" if max_sal else f"> birr {min_sal}"

        rows = [
            e for e in employees
            if e.custom_basic_salary and e.custom_basic_salary >= min_sal and (max_sal is None or e.custom_basic_salary <= max_sal)
        ]

        m, f, t = mf_count(rows)
        total_m += m
        total_f += f
        total_t += t

        data.append(row(label, m, f, t, indent=1))

    data.append(row("Total", total_m, total_f, total_t, indent=1, bold=1))
    return data


# ----------------------------------
# Education Statistics
# ----------------------------------
def education_statistics(filters=None):
    data = []
    data.append({"category": "In Education Permanent Employees", "is_group": 1})
    total_m = total_f = total_t = 0

    emp_filters = get_employee_filters(filters)

    level_map = {
        "Acadamy": ["8th Complete", "5th complete", "6th complete", "7th complete", "9th complete"],
        "10th  new & 12th old complete": ["10th new", "12th old complete", "11th complete"],
        "12th new complete": ["12th complete"],
        "10+1 (Level 1)": ["10+1", "Level I"],
        "10+2 (Level 2)": ["10+2", "Level II"],
        "10+3 (Level 3), Diploma": ["10+3", "Diploma", "Level III", "10+3 (Diploma)"],
        "Advance diploma (level IV)": ["Advance Diploma", "Level IV", "Level V"],
        "BA, BSC, BED (Level V)": ["BA", "BSC", "BED", "BA Degree"],
        "MA, MBA, MS, MSC": ["MA", "MBA", "MS", "MSc", "MSC"],
    }

    for label, levels in level_map.items():
        rows = frappe.db.sql("""
            SELECT DISTINCT e.name, e.gender
            FROM `tabEmployee` e
            INNER JOIN `tabEmployee Education` ed ON ed.parent = e.name
            WHERE ed.level IN %(levels)s
            AND ed.idx = 1
            AND (%(status)s IS NULL OR e.status = %(status)s)
            AND (%(employment_type)s IS NULL OR e.employment_type = %(employment_type)s)
        """, {
            "levels": tuple(levels),
            "status": emp_filters.get("status"),
            "employment_type": emp_filters.get("employment_type")
        }, as_dict=True)

        if not rows:
            continue

        m, f, t = mf_count(rows)
        total_m += m
        total_f += f
        total_t += t
        data.append(row(label, m, f, t, indent=1))

    data.append(row("Total", total_m, total_f, total_t, indent=1, bold=1))
    return data


# ----------------------------------
# Man Power Statistics
# ----------------------------------
def manpower_statistics(filters=None):
    data = []
    data.append({"category": "Man Power Statistical Data", "is_group": 1})
    total_m = total_f = total_t = 0

    for emp_type in ["ቋሚ", "ኮንትራት"]:
        emp_filters = get_employee_filters(filters)
        emp_filters["employment_type"] = emp_type

        rows = frappe.get_all("Employee", filters=emp_filters, fields=["gender"])

        m, f, t = mf_count(rows)
        total_m += m
        total_f += f
        total_t += t
        data.append(row(emp_type, m, f, t, indent=1))

    data.append(row("Total", total_m, total_f, total_t, indent=1, bold=1))
    return data


# ----------------------------------
# Experience Statistics
# ----------------------------------
def experience_statistics(filters=None):
    data = []
    data.append({"category": "Employees Statistical Data In Experience", "is_group": 1})
    total_m = total_f = total_t = 0

    employees = frappe.get_all(
        "Employee",
        fields=["gender", "date_of_joining"],
        filters=get_employee_filters(filters),
    )

    ranges = [
        ("No Experience", 0, 0),
        ("From 1 – 5", 1, 5),
        ("From 6 – 10", 6, 10),
        ("From 11 – 15", 11, 15),
        ("From 16 – 20", 16, 20),
        ("From 21 – 25", 21, 25),
        ("From 26 – 30", 26, 30),
        ("From 31 – 35", 31, 35),
    ]

    for label, min_y, max_y in ranges:
        rows = []
        for e in employees:
            if not e.date_of_joining:
                continue
            years = date_diff(nowdate(), e.date_of_joining) / 365
            if min_y <= years <= max_y:
                rows.append(e)

        m, f, t = mf_count(rows)
        total_m += m
        total_f += f
        total_t += t
        data.append(row(label, m, f, t, indent=1))

    data.append(row("Total", total_m, total_f, total_t, indent=1, bold=1))
    return data


# ----------------------------------
# Age Statistics
# ----------------------------------
def age_statistics(filters=None):
    data = []
    data.append({"category": "Employees Statistical Data By Age", "is_group": 1})
    total_m = total_f = total_t = 0

    employees = frappe.get_all(
        "Employee",
        fields=["gender", "date_of_birth"],
        filters=get_employee_filters(filters),
    )

    age_ranges = [
        ("19 – 25", 19, 25),
        ("26 – 30", 26, 30),
        ("31 – 35", 31, 35),
        ("36 – 40", 36, 40),
        ("41 – 45", 41, 45),
        ("46 – 50", 46, 50),
        ("51 – 55", 51, 55),
        ("56 – 60", 56, 60),
    ]

    for label, min_age, max_age in age_ranges:
        rows = []
        for e in employees:
            if not e.date_of_birth:
                continue
            age = (getdate(today()) - e.date_of_birth).days // 365
            if min_age <= age <= max_age:
                rows.append(e)

        m, f, t = mf_count(rows)
        total_m += m
        total_f += f
        total_t += t
        data.append(row(label, m, f, t, indent=1))

    data.append(row("Total", total_m, total_f, total_t, indent=1, bold=1))
    return data


# ----------------------------------
# Department Statistics
# ----------------------------------
def department_statistics(filters=None):
    data = []
    data.append({"category": "Total Employees with Department", "is_group": 1})
    total_m = total_f = total_t = 0

    for dep in frappe.get_all("Department", pluck="name"):
        emp_filters = get_employee_filters(filters)
        emp_filters["department"] = dep

        rows = frappe.get_all("Employee", filters=emp_filters, fields=["gender"])
        if not rows:
            continue

        m, f, t = mf_count(rows)
        total_m += m
        total_f += f
        total_t += t
        data.append(row(dep, m, f, t, indent=1))

    data.append(row("Total", total_m, total_f, total_t, indent=1, bold=1))
    return data


# ----------------------------------
# Designation Statistics
# ----------------------------------
def designation_statistics(filters=None):
    data = []
    data.append({"category": "Total Employees with Designation", "is_group": 1})
    total_m = total_f = total_t = 0

    for des in frappe.get_all("Designation", pluck="name"):
        emp_filters = get_employee_filters(filters)
        emp_filters["designation"] = des

        rows = frappe.get_all("Employee", filters=emp_filters, fields=["gender"])
        if not rows:
            continue

        m, f, t = mf_count(rows)
        total_m += m
        total_f += f
        total_t += t
        data.append(row(des, m, f, t, indent=1))

    data.append(row("Total", total_m, total_f, total_t, indent=1, bold=1))
    return data