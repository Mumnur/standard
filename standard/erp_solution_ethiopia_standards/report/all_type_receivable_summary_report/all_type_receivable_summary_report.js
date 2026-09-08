frappe.query_reports["All Type Receivable Summary Report"] = {

    filters: [

        {
            fieldname: "reporting_date",

            label: __("Reporting Date"),

            fieldtype: "Date",

            reqd: 1,

            default: frappe.datetime.get_today()
        }

    ],


    formatter: function(
        value,
        row,
        column,
        data,
        default_formatter
    ) {

        value = default_formatter(
            value,
            row,
            column,
            data
        );


        // ----------------------------------------------------
        // Highlight Total Receivable
        // ----------------------------------------------------

        if (
            column.fieldname === "total_receivable"

            && data

            && data.total_receivable
        ) {

            value =
                `<span style="font-weight:700;">
                    ${value}
                </span>`;
        }


        return value;
    }

};