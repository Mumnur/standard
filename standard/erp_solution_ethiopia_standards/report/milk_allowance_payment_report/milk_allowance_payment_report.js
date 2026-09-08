frappe.query_reports["Milk Allowance Payment Report"] = {
    filters: [
        {
            fieldname: "budget_year",
            label: "Budget Year",
            fieldtype: "Link",
            options: "Budget Year"
        },
        {
            fieldname: "month",
            label: "Month",
            fieldtype: "Link",
            options: "Budget Month"
        },
        {
            fieldname: "employee_id",
            label: "Employee",
            fieldtype: "Link",
            options: "Employee"
        },
        {
            fieldname: "department",
            label: "Department",
            fieldtype: "Link",
            options: "Department"
        },
        {
            fieldname: "designation",
            label: "Designation",
            fieldtype: "Link",
            options: "Designation"
        }
    ]
};