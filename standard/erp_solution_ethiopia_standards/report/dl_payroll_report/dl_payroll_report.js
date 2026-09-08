frappe.query_reports["DL Payroll Report"] = {

    // ============================================================
    // FILTERS
    // ============================================================

    filters: [

        {
            fieldname: "budget_month",
            label: __("Budget Month"),
            fieldtype: "Link",
            options: "Budget Month",
            reqd: 0
        },

        {
            fieldname: "budget_year",
            label: __("Budget Year"),
            fieldtype: "Link",
            options: "Budget Year",
            reqd: 0
        },

        {
            fieldname: "daily_labor_salary",
            label: __("Daily Labor Salary"),
            fieldtype: "Link",
            options: "Daily Labor Salary",
            reqd: 0
        },

        {
            fieldname: "report_type",
            label: __("Report Type"),
            fieldtype: "Select",
            options: [
                "Payroll Summary",
                "Bank Final"
            ].join("\n"),
            default: "Payroll Summary",
            reqd: 1
        }

    ],


    // ============================================================
    // ONLOAD
    // ============================================================

    onload: function(report) {

        report.page.add_inner_button(
            __("Clear Filters"),
            function() {

                report.set_filter_value(
                    "budget_month",
                    ""
                );

                report.set_filter_value(
                    "budget_year",
                    ""
                );

                report.set_filter_value(
                    "daily_labor_salary",
                    ""
                );

                report.set_filter_value(
                    "report_type",
                    "Payroll Summary"
                );

                report.refresh();
            }
        );
    },


    // ============================================================
    // AFTER REFRESH
    // ============================================================

    after_refresh: function(report) {

        let values = report.get_values();

        let report_type =
            values.report_type || "Payroll Summary";


        if (report_type === "Bank Final") {

            report.page.set_title(
                __("DL Payroll Report - Bank Final")
            );

        } else {

            report.page.set_title(
                __("DL Payroll Report - Payroll Summary")
            );
        }
    }

};
