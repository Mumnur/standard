import frappe

@frappe.whitelist()
def get_items(source_name):

    fuel_request = frappe.get_doc(
        "Fuel Request Form",
        source_name
    )

    return {
        "project": fuel_request.location,
        "warehouse": fuel_request.warehouse,

        "custom_reference_document": "Fuel Request Form",
        "custom_reference_no": fuel_request.name,

        "stock_entry_type": "Material Issue",

        "item": {
            "item_code": fuel_request.item_code,
            "item_name": fuel_request.item_name,
            "qty": fuel_request.fuel_requested,
            "uom": fuel_request.uom,
            "conversion_factor": 1,
            "warehouse": fuel_request.warehouse
        }
    }