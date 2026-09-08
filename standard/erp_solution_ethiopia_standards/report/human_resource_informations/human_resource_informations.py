

# import frappe
# from frappe import _
# from frappe.utils import getdate, nowdate


# def execute(filters=None):
# 	filters = filters or {}
# 	columns = get_columns()
# 	data = get_data(filters)
# 	return columns, data


# def get_columns():
# 	return [
# 		{"label": _("Employee"), "fieldname": "name", "fieldtype": "Link",
# 			"options": "Employee", "width": 110},
# 		{"label": _("Employee Number"), "fieldname": "employee_number", "fieldtype": "Data", "width": 110},
# 		{"label": _("Full Name"), "fieldname": "employee_name", "fieldtype": "Data", "width": 170},
# 		{"label": _("Gender"), "fieldname": "gender", "fieldtype": "Link",
# 			"options": "Gender", "width": 90},
# 		{"label": _("Date of Birth"), "fieldname": "date_of_birth", "fieldtype": "Date", "width": 100},
# 		{"label": _("Age"), "fieldname": "age", "fieldtype": "Int", "width": 60},
# 		{"label": _("Birth Date (EC)"), "fieldname": "custom_birth_date_ec", "fieldtype": "Data", "width": 100},
# 		{"label": _("Date of Joining"), "fieldname": "date_of_joining", "fieldtype": "Date", "width": 105},
# 		{"label": _("Company"), "fieldname": "company", "fieldtype": "Link",
# 			"options": "Company", "width": 150},
# 		{"label": _("Branch"), "fieldname": "custom_branch", "fieldtype": "Link",
# 			"options": "Company Branch", "width": 120},
# 		{"label": _("Department"), "fieldname": "department", "fieldtype": "Link",
# 			"options": "Department", "width": 160},
# 		{"label": _("Designation"), "fieldname": "designation", "fieldtype": "Link",
# 			"options": "Designation", "width": 140},
# 		{"label": _("Employment Type"), "fieldname": "employment_type", "fieldtype": "Link",
# 			"options": "Employment Type", "width": 120},
# 		{"label": _("Project"), "fieldname": "custom_project", "fieldtype": "Link",
# 			"options": "Project", "width": 140},
# 		{"label": _("Grade"), "fieldname": "grade", "fieldtype": "Link",
# 			"options": "Employee Grade", "width": 100},
# 		{"label": _("Status"), "fieldname": "status", "fieldtype": "Data", "width": 90},
# 		{"label": _("Mobile"), "fieldname": "cell_number", "fieldtype": "Data", "width": 120},
# 		{"label": _("User ID"), "fieldname": "user_id", "fieldtype": "Link",
# 			"options": "User", "width": 160},
# 		{"label": _("Basic Salary"), "fieldname": "custom_basic_salary", "fieldtype": "Currency", "width": 110},
# 		{"label": _("Pension"), "fieldname": "custom_pension", "fieldtype": "Check", "width": 80},
# 		{"label": _("TIN Number"), "fieldname": "custom_tin_number", "fieldtype": "Data", "width": 110},
# 		{"label": _("Pension Number"), "fieldname": "custom_pension_number", "fieldtype": "Data", "width": 110},
# 		{"label": _("Relieving Date"), "fieldname": "relieving_date", "fieldtype": "Date", "width": 100},
# 	]


# def get_data(filters):
# 	conditions, values, date_fieldname = get_conditions(filters)

# 	fields = [
# 		"name", "employee_number", "employee_name", "gender", "date_of_birth",
# 		"custom_birth_date_ec", "date_of_joining", "company", "custom_branch",
# 		"department", "designation", "employment_type", "custom_project", "grade",
# 		"status", "cell_number", "user_id", "custom_basic_salary", "custom_pension",
# 		"custom_tin_number", "custom_pension_number", "relieving_date",
# 	]

# 	query = """
# 		SELECT {fields}
# 		FROM `tabEmployee`
# 		WHERE 1=1 {conditions}
# 		ORDER BY {date_field} ASC, employee_name ASC
# 	""".format(fields=", ".join(fields), conditions=conditions, date_field=date_fieldname)

# 	data = frappe.db.sql(query, values, as_dict=1)

# 	for row in data:
# 		row["age"] = calculate_age(row.get("date_of_birth"))

# 	return data


# def calculate_age(dob):
# 	"""Return completed years of age as of today, based on date_of_birth."""
# 	if not dob:
# 		return None

# 	dob = getdate(dob)
# 	today = getdate(nowdate())

# 	age = today.year - dob.year
# 	if (today.month, today.day) < (dob.month, dob.day):
# 		age -= 1

# 	return age


# def get_conditions(filters):
# 	"""Build parameterized SQL conditions (avoids SQL injection risk)."""
# 	conditions = ""
# 	values = {}

# 	# Employee Status: All Employee / Active Employee / Left Employee
# 	# Decides both the status filter (if any) and which date column
# 	# (date_of_joining vs relieving_date) the From/To Date range applies to.
# 	employee_status = filters.get("employee_status") or "All Employee"

# 	if employee_status == "Active Employee":
# 		conditions += " AND status = %(emp_status)s"
# 		values["emp_status"] = "Active"
# 		date_fieldname = "date_of_joining"
# 	elif employee_status == "Left Employee":
# 		conditions += " AND status = %(emp_status)s"
# 		values["emp_status"] = "Left"
# 		date_fieldname = "relieving_date"
# 	else:  # All Employee
# 		date_fieldname = "date_of_joining"

# 	# Date range filter, applied against the date column chosen above
# 	# (Gregorian dates arrive already converted from EC by the client)
# 	if filters.get("from_date"):
# 		conditions += " AND {0} >= %(from_date)s".format(date_fieldname)
# 		values["from_date"] = filters.get("from_date")

# 	if filters.get("to_date"):
# 		conditions += " AND {0} <= %(to_date)s".format(date_fieldname)
# 		values["to_date"] = filters.get("to_date")

# 	if filters.get("company"):
# 		conditions += " AND company = %(company)s"
# 		values["company"] = filters.get("company")

# 	if filters.get("branch"):
# 		conditions += " AND custom_branch = %(branch)s"
# 		values["branch"] = filters.get("branch")

# 	if filters.get("department"):
# 		conditions += " AND department = %(department)s"
# 		values["department"] = filters.get("department")

# 	if filters.get("designation"):
# 		conditions += " AND designation = %(designation)s"
# 		values["designation"] = filters.get("designation")

# 	if filters.get("employment_type"):
# 		conditions += " AND employment_type = %(employment_type)s"
# 		values["employment_type"] = filters.get("employment_type")

# 	if filters.get("project"):
# 		conditions += " AND custom_project = %(project)s"
# 		values["project"] = filters.get("project")

# 	if filters.get("grade"):
# 		conditions += " AND grade = %(grade)s"
# 		values["grade"] = filters.get("grade")

# 	# Legacy detailed status filter (Active/Inactive/Suspended/Left) only
# 	# applies when "All Employee" is selected, to avoid conflicting with
# 	# the status condition already set above.
# 	if filters.get("status") and employee_status == "All Employee":
# 		conditions += " AND status = %(status)s"
# 		values["status"] = filters.get("status")

# 	return conditions, values, date_fieldname
import frappe
from frappe import _
from frappe.utils import getdate, nowdate


def execute(filters=None):
	filters = filters or {}
	columns = get_columns()
	data = get_data(filters)
	report_summary = get_report_summary(data)
	chart = get_chart_data(data)
	return columns, data, None, chart, report_summary


def get_columns():
	return [
		{"label": _("Employee"), "fieldname": "name", "fieldtype": "Link",
			"options": "Employee", "width": 110},
		{"label": _("Employee Number"), "fieldname": "employee_number", "fieldtype": "Data", "width": 110},
		{"label": _("Full Name"), "fieldname": "employee_name", "fieldtype": "Data", "width": 170},
		{"label": _("Gender"), "fieldname": "gender", "fieldtype": "Link",
			"options": "Gender", "width": 90},
		{"label": _("Date of Birth"), "fieldname": "date_of_birth", "fieldtype": "Date", "width": 100},
		{"label": _("Age"), "fieldname": "age", "fieldtype": "Int", "width": 60},
		{"label": _("Birth Date (EC)"), "fieldname": "custom_birth_date_ec", "fieldtype": "Data", "width": 100},
		{"label": _("Date of Joining"), "fieldname": "date_of_joining", "fieldtype": "Date", "width": 105},
		{"label": _("Company"), "fieldname": "company", "fieldtype": "Link",
			"options": "Company", "width": 150},
		{"label": _("Branch"), "fieldname": "custom_branch", "fieldtype": "Link",
			"options": "Company Branch", "width": 120},
		{"label": _("Department"), "fieldname": "department", "fieldtype": "Link",
			"options": "Department", "width": 160},
		{"label": _("Designation"), "fieldname": "designation", "fieldtype": "Link",
			"options": "Designation", "width": 140},
		{"label": _("Employment Type"), "fieldname": "employment_type", "fieldtype": "Link",
			"options": "Employment Type", "width": 120},
		{"label": _("Project"), "fieldname": "custom_project", "fieldtype": "Link",
			"options": "Project", "width": 140},
		{"label": _("Grade"), "fieldname": "grade", "fieldtype": "Link",
			"options": "Employee Grade", "width": 100},
		{"label": _("Status"), "fieldname": "status", "fieldtype": "Data", "width": 90},
		{"label": _("Mobile"), "fieldname": "cell_number", "fieldtype": "Data", "width": 120},
		{"label": _("User ID"), "fieldname": "user_id", "fieldtype": "Link",
			"options": "User", "width": 160},
		{"label": _("Basic Salary"), "fieldname": "custom_basic_salary", "fieldtype": "Currency", "width": 110},
		{"label": _("Pension"), "fieldname": "custom_pension", "fieldtype": "Check", "width": 80},
		{"label": _("TIN Number"), "fieldname": "custom_tin_number", "fieldtype": "Data", "width": 110},
		{"label": _("Pension Number"), "fieldname": "custom_pension_number", "fieldtype": "Data", "width": 110},
		{"label": _("Relieving Date"), "fieldname": "relieving_date", "fieldtype": "Date", "width": 100},
	]


def get_data(filters):
	conditions, values, date_fieldname = get_conditions(filters)

	fields = [
		"name", "employee_number", "employee_name", "gender", "date_of_birth",
		"custom_birth_date_ec", "date_of_joining", "company", "custom_branch",
		"department", "designation", "employment_type", "custom_project", "grade",
		"status", "cell_number", "user_id", "custom_basic_salary", "custom_pension",
		"custom_tin_number", "custom_pension_number", "relieving_date",
	]

	query = """
		SELECT {fields}
		FROM `tabEmployee`
		WHERE 1=1 {conditions}
		ORDER BY {date_field} ASC, employee_name ASC
	""".format(fields=", ".join(fields), conditions=conditions, date_field=date_fieldname)

	data = frappe.db.sql(query, values, as_dict=1)

	for row in data:
		row["age"] = calculate_age(row.get("date_of_birth"))

	return data


def calculate_age(dob):
	"""Return completed years of age as of today, based on date_of_birth."""
	if not dob:
		return None

	dob = getdate(dob)
	today = getdate(nowdate())

	age = today.year - dob.year
	if (today.month, today.day) < (dob.month, dob.day):
		age -= 1

	return age


def get_report_summary(data):
	"""Cards shown at the top of the report (Total / Male / Female / Other)."""
	total = len(data)
	male = len([d for d in data if d.get("gender") == "ወንድ"])
	female = len([d for d in data if d.get("gender") == "ሴት"])
	other = total - male - female

	summary = [
		{"value": total, "label": _("Total Employees"), "datatype": "Int", "indicator": "Blue"},
		{"value": male, "label": _("Male"), "datatype": "Int", "indicator": "Blue"},
		{"value": female, "label": _("Female"), "datatype": "Int", "indicator": "Pink"},
	]

	if other:
		summary.append({
			"value": other,
			"label": _("Other / Not Specified"),
			"datatype": "Int",
			"indicator": "Grey",
		})

	return summary


def get_chart_data(data):
	"""Donut chart of gender distribution."""
	gender_counts = {}
	for row in data:
		g = row.get("gender") or _("Not Specified")
		gender_counts[g] = gender_counts.get(g, 0) + 1

	return {
		"data": {
			"labels": list(gender_counts.keys()),
			"datasets": [{"name": _("Employees"), "values": list(gender_counts.values())}],
		},
		"type": "donut",
		"colors": ["#5e64ff", "#ff5858", "#ffa00a", "#98d85b"],
	}


def get_conditions(filters):
	"""Build parameterized SQL conditions (avoids SQL injection risk)."""
	conditions = ""
	values = {}

	# Employee Status: All Employee / Active Employee / Left Employee
	# Decides both the status filter (if any) and which date column
	# (date_of_joining vs relieving_date) the From/To Date range applies to.
	employee_status = filters.get("employee_status") or "All Employee"

	if employee_status == "Active Employee":
		conditions += " AND status = %(emp_status)s"
		values["emp_status"] = "Active"
		date_fieldname = "date_of_joining"
	elif employee_status == "Left Employee":
		conditions += " AND status = %(emp_status)s"
		values["emp_status"] = "Left"
		date_fieldname = "relieving_date"
	else:  # All Employee
		date_fieldname = "date_of_joining"

	# Date range filter, applied against the date column chosen above
	# (Gregorian dates arrive already converted from EC by the client)
	if filters.get("from_date"):
		conditions += " AND {0} >= %(from_date)s".format(date_fieldname)
		values["from_date"] = filters.get("from_date")

	if filters.get("to_date"):
		conditions += " AND {0} <= %(to_date)s".format(date_fieldname)
		values["to_date"] = filters.get("to_date")

	if filters.get("company"):
		conditions += " AND company = %(company)s"
		values["company"] = filters.get("company")

	if filters.get("branch"):
		conditions += " AND custom_branch = %(branch)s"
		values["branch"] = filters.get("branch")

	if filters.get("department"):
		conditions += " AND department = %(department)s"
		values["department"] = filters.get("department")

	if filters.get("designation"):
		conditions += " AND designation = %(designation)s"
		values["designation"] = filters.get("designation")

	if filters.get("employment_type"):
		conditions += " AND employment_type = %(employment_type)s"
		values["employment_type"] = filters.get("employment_type")

	if filters.get("project"):
		conditions += " AND custom_project = %(project)s"
		values["project"] = filters.get("project")

	if filters.get("grade"):
		conditions += " AND grade = %(grade)s"
		values["grade"] = filters.get("grade")

	if filters.get("gender"):
		conditions += " AND gender = %(gender)s"
		values["gender"] = filters.get("gender")

	# Legacy detailed status filter (Active/Inactive/Suspended/Left) only
	# applies when "All Employee" is selected, to avoid conflicting with
	# the status condition already set above.
	if filters.get("status") and employee_status == "All Employee":
		conditions += " AND status = %(status)s"
		values["status"] = filters.get("status")

	return conditions, values, date_fieldname