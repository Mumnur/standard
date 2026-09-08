frappe.query_reports["Employee Attendance Summary Report"] = {
    filters: [
        {
            fieldname: "view",
            label: "View",
            fieldtype: "Select",
            options: ["Summary", "Detail"],
            default: "Summary",
            reqd: 1
        },
        {
            fieldname: "company_branch",
            label: "Company Branch",
            fieldtype: "Link",
            options: "Company Branch"
        },
        {
            fieldname: "employment_type",
            label: "Employment Type",
            fieldtype: "Link",
            options: "Employment Type"
        },
        {
            fieldname: "budget_year",
            label: "Budget Year",
            fieldtype: "Link",
            options: "Budget Year"
        },
        {
            fieldname: "budget_month",
            label: "Budget Month",
            fieldtype: "Link",
            options: "Budget Month"
        },
        {
            fieldname: "employee_id",
            label: "Employee",
            fieldtype: "Link",
            options: "Employee"
        }
    ]
};