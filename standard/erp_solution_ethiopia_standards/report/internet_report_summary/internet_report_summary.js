frappe.query_reports["Internet Report Summary"] = {
    filters: [
        {
            fieldname: "group_by",
            label: "Group By",
            fieldtype: "Select",
            options: ["Department", "Work Place"],
            default: "Department",
            reqd: 1
        },
        {
            fieldname: "budget_year",
            label: "Budget Year",
            fieldtype: "Link",
            options: "Budget Year"
        },
        {
            fieldname: "month",
            label: "Budget Month",
            fieldtype: "Link",
            options: "Budget Month"
        },
        {
            fieldname: "department",
            label: "Department",
            fieldtype: "Link",
            options: "Department"
        },
        {
            fieldname: "work_place",
            label: "Work Place",
            fieldtype: "Link",
            options: "Project"
        }
    ]
};