frappe.provide("standard.stock_ledger_custom");

frappe.query_reports["Stock Ledger"] = {
    filters: [
        {
            fieldname: "company",
            label: __("Company"),
            fieldtype: "Link",
            options: "Company",
            default: frappe.defaults.get_user_default("Company"),
            reqd: 1,
        },

        // -----------------------------------------
        // Ethiopian From Date
        // -----------------------------------------
        {
            fieldname: "from_date_ec",
            label: __("From Date (E.C.)"),
            fieldtype: "Data",
            reqd: 1,

            change: function () {
                ConvertFromDate(frappe.query_report);
            },
        },

        // -----------------------------------------
        // Gregorian From Date
        // -----------------------------------------
        {
            fieldname: "from_date",
            label: __("From Date"),
            fieldtype: "Date",
            default: frappe.datetime.add_months(
                frappe.datetime.get_today(),
                -1
            ),
            reqd: 1,
        },

        // -----------------------------------------
        // Ethiopian To Date
        // -----------------------------------------
        {
            fieldname: "to_date_ec",
            label: __("To Date (E.C.)"),
            fieldtype: "Data",
            reqd: 1,

            change: function () {
                ConvertToDate(frappe.query_report);
            },
        },

        // -----------------------------------------
        // Gregorian To Date
        // -----------------------------------------
        {
            fieldname: "to_date",
            label: __("To Date"),
            fieldtype: "Date",
            default: frappe.datetime.get_today(),
            reqd: 1,
        },

        {
            fieldname: "warehouse",
            label: __("Warehouses"),
            fieldtype: "MultiSelectList",
            options: "Warehouse",

            get_data: function (txt) {
                const company =
                    frappe.query_report.get_filter_value("company");

                return frappe.db.get_link_options(
                    "Warehouse",
                    txt,
                    {
                        company: company,
                    }
                );
            },
        },

        {
            fieldname: "item_code",
            label: __("Items"),
            fieldtype: "MultiSelectList",
            options: "Item",

            get_data: async function (txt) {
                let { message: data } = await frappe.call({
                    method: "erpnext.controllers.queries.item_query",

                    args: {
                        doctype: "Item",
                        txt: txt,
                        searchfield: "name",
                        start: 0,
                        page_len: 10,
                        filters: {},
                        as_dict: 1,
                    },
                });

                data = data.map(({ name, ...rest }) => {
                    return {
                        value: name,
                        description: Object.values(rest),
                    };
                });

                return data || [];
            },
        },

        {
            fieldname: "item_group",
            label: __("Item Group"),
            fieldtype: "Link",
            options: "Item Group",
        },

        {
            fieldname: "batch_no",
            label: __("Batch No"),
            fieldtype: "Link",
            options: "Batch",

            on_change() {
                const batch_no =
                    frappe.query_report.get_filter_value("batch_no");

                if (batch_no) {
                    frappe.query_report.set_filter_value(
                        "segregate_serial_batch_bundle",
                        1
                    );
                } else {
                    frappe.query_report.set_filter_value(
                        "segregate_serial_batch_bundle",
                        0
                    );
                }
            },
        },

        {
            fieldname: "brand",
            label: __("Brand"),
            fieldtype: "Link",
            options: "Brand",
        },

        {
            fieldname: "voucher_no",
            label: __("Voucher #"),
            fieldtype: "Data",
        },

        {
            fieldname: "project",
            label: __("Project"),
            fieldtype: "Link",
            options: "Project",
        },

        {
            fieldname: "include_uom",
            label: __("Include UOM"),
            fieldtype: "Link",
            options: "UOM",
        },

        {
            fieldname: "valuation_field_type",
            label: __("Valuation Field Type"),
            fieldtype: "Select",
            width: "80",
            options: "Currency\nFloat",
            default: "Currency",
        },

        {
            fieldname: "segregate_serial_batch_bundle",
            label: __("Enable Serial / Batch Bundle"),
            fieldtype: "Check",
            default: 0,
        },
    ],

    formatter: function (
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
            column.fieldname == "out_qty" &&
            data &&
            data.out_qty < 0
        ) {
            value =
                "<span style='color:red'>" +
                value +
                "</span>";
        } else if (
            column.fieldname == "in_qty" &&
            data &&
            data.in_qty > 0
        ) {
            value =
                "<span style='color:green'>" +
                value +
                "</span>";
        }

        return value;
    },

    onload: function (report) {

        // -----------------------------------------
        // Original v16 Stock Balance button
        // -----------------------------------------

        report.page.add_inner_button(
            __("View Stock Balance"),
            function () {

                var filters = report.get_values();

                frappe.set_route(
                    "query-report",
                    "Stock Balance",
                    filters
                );
            }
        );

        // -----------------------------------------
        // Set Ethiopian From Date
        // -----------------------------------------

        const fromDate =
            report.get_filter_value("from_date");

        if (fromDate) {

            const [year, month, day] =
                toEC(
                    fromDate
                        .split("-")
                        .map(Number)
                );

            const ecDateFrom =
                `${String(day).padStart(2, "0")}/${String(month).padStart(2, "0")}/${year}`;

            report.set_filter_value(
                "from_date_ec",
                ecDateFrom
            );
        }

        // -----------------------------------------
        // Set Ethiopian To Date
        // -----------------------------------------

        const toDate =
            report.get_filter_value("to_date");

        if (toDate) {

            const [year, month, day] =
                toEC(
                    toDate
                        .split("-")
                        .map(Number)
                );

            const ecDateTo =
                `${String(day).padStart(2, "0")}/${String(month).padStart(2, "0")}/${year}`;

            report.set_filter_value(
                "to_date_ec",
                ecDateTo
            );
        }
    },
};


// -----------------------------------------
// Keep original v16 Inventory Dimensions
// -----------------------------------------

erpnext.utils.add_inventory_dimensions(
    "Stock Ledger",
    10
);


// =================================================
// Ethiopian From Date → Gregorian From Date
// =================================================

function ConvertFromDate(report) {

    const ecDate =
        report.get_filter_value("from_date_ec");

    if (!ecDate) {
        return;
    }

    const [day, month, year] =
        ecDate.split("/").map(Number);

    const gcDate =
        toGC([year, month, day]);

    const gregorianDate =
        `${gcDate[0]}-${String(gcDate[1]).padStart(2, "0")}-${String(gcDate[2]).padStart(2, "0")}`;

    report.set_filter_value(
        "from_date",
        gregorianDate
    );
}


// =================================================
// Ethiopian To Date → Gregorian To Date
// =================================================

function ConvertToDate(report) {

    const ecDate =
        report.get_filter_value("to_date_ec");

    if (!ecDate) {
        return;
    }

    const [day, month, year] =
        ecDate.split("/").map(Number);

    const gcDate =
        toGC([year, month, day]);

    const gregorianDate =
        `${gcDate[0]}-${String(gcDate[1]).padStart(2, "0")}-${String(gcDate[2]).padStart(2, "0")}`;

    report.set_filter_value(
        "to_date",
        gregorianDate
    );
}