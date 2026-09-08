// Copyright (c) 2026, ERP Solution Ethiopia PLC
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Uniform Registration Wcc Summary"] = {
	"filters": [
		{
			"label": "Project",
			"fieldname": "project",
			"fieldtype": "Link",
			"options": "Project"
		},
		{
			"label": "Employee",
			"fieldname": "employee",
			"fieldtype": "Link",
			"options": "Employee"
		},
		{
			"label": "Budget Year",
			"fieldname": "budget_year",
			"fieldtype": "Link",
			"options": "Budget Year"
		},
		{
			"label": "Gender",
			"fieldname": "gender",
			"fieldtype": "Link",
			"options": "Gender"
		},
		{
			"label": "Designation",
			"fieldname": "designation",
			"fieldtype": "Link",
			"options": "Designation"
		}
	]
}