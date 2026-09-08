frappe.query_reports["Accrued Severance Payable Report"] = {
    filters: [
        {
            fieldname: "reporting_date",
            label: __("Reporting Date"),
            fieldtype: "Date",
            reqd: 1,
            default: frappe.datetime.get_today()
        }
    ],

    formatter: function (value, row, column, data, default_formatter) {
        value = default_formatter(value, row, column, data);

        // Highlight Total EV
        if (column.fieldname === "total_ev" && data) {
            value = `<b>${value}</b>`;
        }

        return value;
    }
};