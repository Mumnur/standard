frappe.ui.form.on("Material Request", {
    setup(frm) {
        frm.set_query("item_code", "items", function (doc, cdt, cdn) {

            // Material Issue and Material Transfer:
            // Allow Maintain Stock + Fixed Asset items
            if (
                doc.material_request_type === "Material Issue" ||
                doc.material_request_type === "Material Transfer"
            ) {
                return {
                    query: "standard.api.item_query.material_request_item_query"
                };
            }

            // Other Material Request types
            let filters = {
                is_stock_item: 1
            };

            if (doc.material_request_type === "Customer Provided") {
                filters.customer = doc.customer;
            }
            else if (
                doc.material_request_type === "Purchase" ||
                doc.material_request_type === "Subcontracting"
            ) {
                filters = {
                    is_purchase_item: 1
                };
            }
            else if (doc.material_request_type === "Manufacture") {
                filters.include_item_in_manufacturing = 1;
            }

            return {
                query: "erpnext.controllers.queries.item_query",
                filters: filters
            };
        });
    }
});