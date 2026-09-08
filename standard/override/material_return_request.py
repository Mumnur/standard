import frappe

@frappe.whitelist()
def get_items(source_name):

    mrr = frappe.get_doc(
        "Material Return Request",
        source_name
    )

    items = []

    for row in mrr.items:

        requested_qty = row.qty or 0
        returned_qty = row.returned_qty or 0

        remaining_qty = requested_qty - returned_qty

        # Only fetch items that still have
        # quantity remaining to be returned
        if remaining_qty > 0:

            items.append({
                "item_code": row.item_code,
                "item_name": row.item_name,
                "qty": remaining_qty,
                "uom": row.uom,
                "conversion_factor": row.conversion_factor,
                "warehouse": (
                    row.warehouse
                    or mrr.set_warehouse
                )
            })

    return {
        "project": mrr.project,

        "to_warehouse": mrr.set_warehouse,

        "custom_reference_document":
            "Material Return Request",

        "custom_reference_no":
            mrr.name,

        "stock_entry_type":
            "Material Receipt",

        "items": items
    }