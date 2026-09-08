frappe.query_reports["Investment Participation"] = {

    filters: [

        {
            fieldname: "fiscal_year",
            label: __("Fiscal Year"),
            fieldtype: "Link",
            options: "Fiscal Year",
            reqd: 1
        }

    ],

    onload: function(report) {

        // ====================================================
        // DEFAULT FISCAL YEAR
        // ====================================================

        frappe.call({

            method:
                "erpnext.accounts.utils.get_fiscal_year",

            args: {
                date: frappe.datetime.get_today()
            },

            callback: function(r) {

                if (!r.message) {
                    return;
                }

                let fiscal_year =
                    r.message[0];

                if (
                    !report.get_values().fiscal_year
                ) {

                    report.set_filter_value(
                        "fiscal_year",
                        fiscal_year
                    );

                }

            }

        });

    },

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

        // ====================================================
        // TOTAL ROW
        // ====================================================

        if (
            data &&
            data.is_total
        ) {

            value =
                "<b>" +
                value +
                "</b>";

        }

        return value;
    }

};