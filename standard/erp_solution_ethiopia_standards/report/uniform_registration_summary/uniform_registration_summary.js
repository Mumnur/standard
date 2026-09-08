// Copyright (c) 2016, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Uniform Registration Summary"] = {
	"filters": [
    {
        "label": "Project",
        "fieldname": "project",
        "fieldtype": "Link",
        "options": "Project"
    },
    {
        "label": "Employee",
        "fieldname": "employee_id",
        "fieldtype": "Link",
        "options": "Employee"
    },
    {
        "label": "Budget Year",
        "fieldname": "budget_year",
        "fieldtype": "Link",
        "options": "Budget Year"
    }
	]
}

