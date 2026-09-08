frappe.query_reports["Employee Summary Report"] = {
	"filters": [
		{
			"fieldname": "company",
			"label": __("Company"),
			"fieldtype": "Link",
			"options": "Company",
			"default": frappe.defaults.get_user_default("Company")
		},
		{
			"fieldname": "department",
			"label": __("Department"),
			"fieldtype": "Link",
			"options": "Department"
		},
		{
			"fieldname": "designation",
			"label": __("Designation"),
			"fieldtype": "Link",
			"options": "Designation"
		},
		{
			"fieldname": "from_date",
			"label": __("From Date"),
			"fieldtype": "Date"
		},
		{
			"fieldname": "to_date",
			"label": __("To Date"),
			"fieldtype": "Date"
		},
		{
			"fieldname": "employment_type",
			"label": __("Employment Type"),
			"fieldtype": "Link",
			"options": "Employment Type"
		},
		// {
		// 	"fieldname": "management_member",
		// 	"label": __("Management Members"),
		// 	"fieldtype": "Select",
		// 	"options": "\nYes\nNo",
		// },
		{
			"fieldname": "status",
			"label": __("Status"),
			"fieldtype": "Select",
			"options": "\nActive\nInactive\nSuspended\nLeft",
			"default": "Active"
		}
	]
};

