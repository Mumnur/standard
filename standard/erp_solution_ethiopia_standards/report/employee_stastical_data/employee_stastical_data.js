frappe.query_reports["Employee Stastical Data"] = {
    "filters": [
        {
            "fieldname": "salary_ranges",
            "label": __("Salary Ranges"),
            "fieldtype": "Data",
            "description": __("Enter comma-separated salary ranges, e.g., 1500-1838,1839-2758,2759-4005")
        },
        {
            "fieldname": "status",
            "label": __("Status"),
            "fieldtype": "Select",
            "options": ["Active", "Left"],
            "default": "Active"
        },
        {
            "fieldname": "employment_type",
            "label": __("Employment Type"),
            "fieldtype": "Link",
            "options": "Employment Type"
        }
        
    ]
};

