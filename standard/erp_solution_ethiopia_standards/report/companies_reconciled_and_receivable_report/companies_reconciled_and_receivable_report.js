frappe.query_reports["Companies Reconciled and Receivable Report"] = {

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
        // Highlight Total Reporting Date Balance
        // ----------------------------------------------------

        if (
            column.fieldname ===
                "total_reporting_date_balance"

            && data

            && data.total_reporting_date_balance
        ) {

            value =
                `<span style="font-weight:600;">
                    ${value}
                </span>`;
        }


        return value;
    }

};