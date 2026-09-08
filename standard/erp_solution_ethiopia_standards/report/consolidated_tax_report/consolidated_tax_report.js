frappe.query_reports["Consolidated Tax Report"] = {

    filters: [

        {
            fieldname: "report_type",
            label: __("Report Type"),
            fieldtype: "Select",
            options: [
                "",
                "3 Withholding Payable",
                "7.5 Withholding Payable",
                "15 VAT Receivable",
                "3 Withholding Receivable",
                "15 VAT Payable",
                "Employee Income Tax",
                "Sales of Bid"
            ].join("\n"),
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
            fieldname: "budget_month",
            label: __("Budget Month"),
            fieldtype: "Link",
            options: "Budget Month",
            reqd: 0
        }

    ],

    onload: function(report) {

        report.page.add_inner_button(
            __("Refresh"),
            function() {
                report.refresh();
            }
        );

    }

};