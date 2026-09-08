frappe.query_reports["Revenue Plan"] = {

    filters: [

        // ====================================================
        // BUDGET YEAR
        // ====================================================

        {
            fieldname: "budget_year",
            label: __("Budget Year"),
            fieldtype: "Link",
            options: "Budget Year",
            reqd: 1
        },

        // ====================================================
        // PERIOD
        // ====================================================

        {
            fieldname: "period",
            label: __("Period"),
            fieldtype: "MultiSelect",
            reqd: 1,

            options: [
                "1",
                "2",
                "3",
                "4",
                "5",
                "6",
                "7",
                "8",
                "9",
                "10",
                "11",
                "12"
            ].join("\n"),

            description: __(
                "Select one or more periods. " +
                "The highest selected period is treated as the current period."
            )
        }

    ],


    // ========================================================
    // ONLOAD
    // ========================================================

    onload: function(report) {

        // ----------------------------------------------------
        // Set default period to 1
        // ----------------------------------------------------

        if (!frappe.query_report.get_filter_value("period")) {

            frappe.query_report.set_filter_value(
                "period",
                "1"
            );

        }

    },


    // ========================================================
    // AFTER REFRESH
    // ========================================================

    after_datatable_render: function(datatable) {

        // ----------------------------------------------------
        // Freeze first column
        // ----------------------------------------------------

        if (datatable) {

            datatable.freezeColumns = 1;

        }

    }

};