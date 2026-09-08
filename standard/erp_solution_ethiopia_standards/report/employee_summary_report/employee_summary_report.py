# Copyright (c) 2015, Frappe Technologies Pvt. Ltd.
# License: GNU General Public License v3

import frappe
from frappe import _
from frappe.utils import getdate, today


def execute(filters=None):
	if not filters:
		filters = {}

	columns = get_columns()
	data = get_data(filters)
	summary = get_summary(data)

	return columns, data,None,None,summary

def get_summary(data):
	total = len(data)
	male = 0
	female = 0

	for row in data:
		if row[2] == "ወንድ":
			male += 1
		elif row[2] == "ሴት":
			female += 1

	return [
		{
			"value": total,
			"label": _("Total Employees"),
			"datatype": "Int"
		},
		{
			"value": male,
			"label": _("Total Male"),
			"datatype": "Int"
		},
		{
			"value": female,
			"label": _("Total Female"),
			"datatype": "Int"
		}
	]
def get_columns():
	return [
		_("Employee") + ":Link/Employee:120",
		_("Full Name (English)") + ":Data:200",
		_("Gender") + ":Link/Gender:90",
		_("Date of Birth") + ":Date:110",
		_("Age") + ":Int:70",
		_("Date of Birth Ec") + ":Data:110",
		_("Date of Joining") + ":Date:110",
		_("Date of Joining Ec") + ":Data:110",
		_("Department") + ":Link/Department:140",
		_("Designation") + ":Link/Designation:140",
		_("Salary") + ":Data:110",
		_("Employement Type") + ":Link/Employment Type:110",
		_("Status") + ":Data:90",
	]


def get_data(filters):
	conditions = get_conditions(filters)

	rows = frappe.db.sql(
		"""
		SELECT
			name,
			employee_name,
			gender,
			date_of_birth,
			custom_birth_date_ec,
			date_of_joining,
			custom_date_of_joining_date_ec,
			department,
			designation,
			custom_basic_salary,
			employment_type,
			status
		FROM `tabEmployee`
		WHERE 1=1 %s
		ORDER BY employee_name
		"""
		% conditions,
		as_list=1
	)
	for row in rows:
		dob = row[3]
		if dob:
			age = (getdate(today()) - getdate(dob)).days // 365
		else:
			age = None

		# Insert Age after Date of Birth
		row.insert(4, age)

	return rows


def get_conditions(filters):
	conditions = ""

	if filters.get("company"):
		conditions += " AND company = '%s'" % filters["company"].replace("'", "\\'")

	if filters.get("department"):
		conditions += " AND department = '%s'" % filters["department"].replace("'", "\\'")

	if filters.get("designation"):
		conditions += " AND designation = '%s'" % filters["designation"].replace("'", "\\'")

	if filters.get("employment_type"):
		conditions += " AND employment_type = '%s'" % filters["employment_type"].replace("'", "\\'")
		
	# if filters.get("management_member"):
	# 	conditions += " AND management_member = '%s'" % filters["management_member"].replace("'", "\\'")
	
	if filters.get("status"):
		conditions += " AND status = '%s'" % filters["status"].replace("'", "\\'")

	if filters.get("from_date"):
		conditions += " AND date_of_joining >= '%s'" % filters["from_date"]

	if filters.get("to_date"):
		conditions += " AND date_of_joining <= '%s'" % filters["to_date"]

	return conditions

