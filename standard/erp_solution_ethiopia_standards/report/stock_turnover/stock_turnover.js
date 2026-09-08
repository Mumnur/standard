frappe.query_reports["Stock Turnover"] = {

    filters: [

        {
            fieldname: "company",
            label: __("Company"),
            fieldtype: "Link",
            options: "Company",
            default: frappe.defaults.get_user_default("Company"),
            reqd: 1
        },

        {
            fieldname: "report_type",
            label: __("Report Type"),
            fieldtype: "Select",
            options: [
                "Company",
                "By Project"
            ],
            default: "Company",
            reqd: 1
        },

        {
            fieldname: "warehouse",
            label: __("Project / Warehouse"),
            fieldtype: "Link",
            options: "Warehouse",
            depends_on:
                "eval:doc.report_type == 'By Project'"
        },

        {
            fieldname: "item_group",
            label: __("Item Group"),
            fieldtype: "Link",
            options: "Item Group"
        },

        {
            fieldname: "item_code",
            label: __("Item"),
            fieldtype: "Link",
            options: "Item"
        },

        {
            fieldname: "from_date",
            label: __("From Date"),
            fieldtype: "Date",
            default:
                erpnext.utils.get_fiscal_year(
                    frappe.datetime.get_today(),
                    true
                )[1],
            reqd: 1
        },

        {
            fieldname: "to_date",
            label: __("To Date"),
            fieldtype: "Date",
            default:
                frappe.datetime.get_today(),
            reqd: 1
        },

        // -----------------------------------------------------
        // Dynamic Turnover Range
        //
        // Example:
        //
        // 2, 4
        //
        // < 2       Low
        // 2 - < 4   Normal
        // >= 4      High
        //
        // Example:
        //
        // 1, 3, 6
        //
        // < 1       Very Low
        // 1 - < 3   Low
        // 3 - < 6   Normal
        // >= 6      High
        // -----------------------------------------------------

        {
            fieldname: "range",
            label: __("Turnover Range"),
            fieldtype: "Data",
            default: "2, 4"
        },

        {
            fieldname: "turnover_level",
            label: __("Turnover Level"),
            fieldtype: "Select",
            options: [
                "All",
                "Very Low",
                "Low",
                "Normal",
                "High",
                "No Movement"
            ],
            default: "All"
        }

    ],

    // ---------------------------------------------------------
    // Onload
    // ---------------------------------------------------------

    onload: function(report) {

        // -----------------------------------------------------
        // Warehouse filter
        // -----------------------------------------------------

        report.page.fields_dict.warehouse.get_query =
            function() {

                let values =
                    report.get_values();

                if (!values.company) {

                    return {};
                }

                return {

                    filters: {

                        company:
                            values.company

                    }

                };

            };


        // -----------------------------------------------------
        // Item filter
        // -----------------------------------------------------

        report.page.fields_dict.item_code.get_query =
            function() {

                return {

                    filters: {

                        disabled: 0

                    }

                };

            };

    },

    // ---------------------------------------------------------
    // Formatter
    // ---------------------------------------------------------

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

        if (!data) {

            return value;
        }

        // -----------------------------------------------------
        // Turnover Ratio
        // -----------------------------------------------------

        if (
            column.fieldname ===
            "turnover_ratio"
        ) {

            let ratio =
                flt(data.turnover_ratio);

            if (ratio >= 4) {

                value =
                    `<span style="
                        color:green;
                        font-weight:bold;
                    ">
                        ${value}
                    </span>`;

            }
            else if (ratio > 0) {

                value =
                    `<span style="
                        color:#b8860b;
                        font-weight:bold;
                    ">
                        ${value}
                    </span>`;

            }
            else {

                value =
                    `<span style="
                        color:red;
                        font-weight:bold;
                    ">
                        ${value}
                    </span>`;

            }

        }

        // -----------------------------------------------------
        // DIO
        // -----------------------------------------------------

        if (
            column.fieldname === "dio"
        ) {

            let dio =
                flt(data.dio);

            if (dio > 180) {

                value =
                    `<span style="
                        color:red;
                        font-weight:bold;
                    ">
                        ${value}
                    </span>`;

            }
            else if (dio > 90) {

                value =
                    `<span style="
                        color:#b8860b;
                        font-weight:bold;
                    ">
                        ${value}
                    </span>`;

            }

        }

        // -----------------------------------------------------
        // Turnover Level
        // -----------------------------------------------------

        if (
            column.fieldname ===
            "turnover_level"
        ) {

            let level =
                data.turnover_level;

            if (level === "High") {

                value =
                    `<span style="
                        color:green;
                        font-weight:bold;
                    ">
                        ${value}
                    </span>`;

            }
            else if (
                level === "Normal"
            ) {

                value =
                    `<span style="
                        color:#b8860b;
                        font-weight:bold;
                    ">
                        ${value}
                    </span>`;

            }
            else if (
                level === "Low" ||
                level === "Very Low"
            ) {

                value =
                    `<span style="
                        color:red;
                        font-weight:bold;
                    ">
                        ${value}
                    </span>`;

            }

        }

        return value;
    }

};