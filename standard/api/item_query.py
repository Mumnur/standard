import frappe


@frappe.whitelist()
@frappe.validate_and_sanitize_search_inputs
def material_request_item_query(
    doctype,
    txt,
    searchfield,
    start,
    page_len,
    filters,
    reference_doctype=None,
    reference_name=None,
):
    return frappe.db.sql(
        """
        SELECT
            i.name,
            i.item_name,
            i.description
        FROM `tabItem` i
        WHERE
            i.disabled = 0
            AND (
                i.is_stock_item = 1
                OR i.is_fixed_asset = 1
            )
            AND (
                i.name LIKE %(txt)s
                OR i.item_name LIKE %(txt)s
            )
        ORDER BY i.name
        LIMIT %(start)s, %(page_len)s
        """,
        {
            "txt": "%" + (txt or "") + "%",
            "start": start,
            "page_len": page_len,
        },
    )