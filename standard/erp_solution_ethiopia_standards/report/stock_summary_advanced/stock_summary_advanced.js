frappe.query_reports["Stock Summary Advanced"] = {

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
            fieldname: "value_or_qty",
            label: __("Show"),
            fieldtype: "Select",
            options: [
                "Qty",
                "Value"
            ],
            default: "Qty",
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
            default: frappe.datetime.get_today(),
            reqd: 1
        }

    ],


    onload: function(report) {

        /*
         * Warehouse filter
         * Only used when Report Type = By Project
         */

        report.page.fields_dict.warehouse.get_query =
            function() {

                let values = report.get_values();

                if (!values.company) {
                    return {};
                }

                return {
                    filters: {
                        company: values.company
                    }
                };
            };


        /*
         * Item filter
         */

        report.page.fields_dict.item_code.get_query =
            function() {

                return {
                    filters: {
                        disabled: 0
                    }
                };
            };

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


        if (!data) {
            return value;
        }


        /*
         * Highlight negative Balance Qty
         */

        if (
            column.fieldname === "bal_qty"
            && flt(data.bal_qty) < 0
        ) {

            value =
                `<span style="color:red;font-weight:bold;">
                    ${value}
                </span>`;
        }


        /*
         * Highlight negative Opening Qty
         */

        if (
            column.fieldname === "opening_qty"
            && flt(data.opening_qty) < 0
        ) {

            value =
                `<span style="color:red;font-weight:bold;">
                    ${value}
                </span>`;
        }


        return value;
    }

};