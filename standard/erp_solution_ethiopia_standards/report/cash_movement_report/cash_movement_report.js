frappe.query_reports["Cash Movement Report"] = {

    filters: [

        // ====================================================
        // FISCAL YEAR
        // ====================================================

        {
            fieldname: "fiscal_year",
            label: __("Fiscal Year"),
            fieldtype: "Link",
            options: "Fiscal Year",
            reqd: 1,

            on_change: function(report) {

                let fiscal_year =
                    report.get_values().fiscal_year;

                if (!fiscal_year) {
                    return;
                }

                frappe.db.get_value(
                    "Fiscal Year",
                    fiscal_year,
                    [
                        "year_start_date",
                        "year_end_date"
                    ],
                    function(r) {

                        if (!r.message) {
                            return;
                        }

                        report.set_filter_value(
                            "from_date",
                            r.message.year_start_date
                        );

                        report.set_filter_value(
                            "to_date",
                            r.message.year_end_date
                        );

                    }
                );
            }
        },

        // ====================================================
        // FROM DATE
        // ====================================================

        {
            fieldname: "from_date",
            label: __("From Date"),
            fieldtype: "Date",
            reqd: 1
        },

        // ====================================================
        // TO DATE
        // ====================================================

        {
            fieldname: "to_date",
            label: __("To Date"),
            fieldtype: "Date",
            reqd: 1
        },

        // ====================================================
        // FROM BRANCH
        // ====================================================

        {
            fieldname: "from_banch",
            label: __("From Branch"),
            fieldtype: "Link",
            options: "Company Branch"
        },

        // ====================================================
        // TO BRANCH
        // ====================================================

        {
            fieldname: "to_banch",
            label: __("To Branch"),
            fieldtype: "Link",
            options: "Company Branch"
        }

    ],

    // ========================================================
    // ONLOAD
    // ========================================================

    onload: function(report) {

        frappe.call({

            method:
                "erpnext.accounts.utils.get_fiscal_year",

            args: {

                date:
                    frappe.datetime.get_today()

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

                    frappe.db.get_value(
                        "Fiscal Year",
                        fiscal_year,
                        [
                            "year_start_date",
                            "year_end_date"
                        ],
                        function(res) {

                            if (!res.message) {
                                return;
                            }

                            report.set_filter_value(
                                "from_date",
                                res.message.year_start_date
                            );

                            report.set_filter_value(
                                "to_date",
                                res.message.year_end_date
                            );

                        }
                    );
                }

            }

        });

    },

    // ========================================================
    // FORMATTER
    // ========================================================

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