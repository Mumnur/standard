frappe.query_reports["Phone Allowance Expiry Alert"] = {
    filters: [
        {
            fieldname: "budget_year",
            label: "Budget Year",
            fieldtype: "Link",
            options: "Budget Year"
        },
        {
            fieldname: "department",
            label: "Department",
            fieldtype: "Link",
            options: "Department"
        }
    ],
    formatter: function (value, row, column, data, default_formatter) {
        value = default_formatter(value, row, column, data);
        if (column.fieldname === "days_remaining" && data.days_remaining !== null) {
            if (data.days_remaining < 0) {
                value = `<span style='color:#e03e2d;font-weight:bold;'>${value}</span>`;
            } else if (data.days_remaining <= 30) {
                value = `<span style='color:#f39c12;font-weight:bold;'>${value}</span>`;
            }
        }
        return value;
    }
};