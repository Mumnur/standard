import frappe
from frappe.desk.reportview import get_match_cond

from erpnext.stock.doctype.material_request.material_request import (
    make_stock_entry as original_make_stock_entry,
)


@frappe.whitelist()
def make_stock_entry(source_name, target_doc=None):

    doc = original_make_stock_entry(
        source_name,
        target_doc
    )

    mr = frappe.get_doc(
        "Material Request",
        source_name
    )


    # Project mapping
    if mr.custom_project:
        doc.project = mr.custom_project


    # Reference information
    doc.custom_reference_no = mr.name
    doc.custom_reference_document = "Material Request"
    # doc.custom_document = "Store Issue Voucher"


    return doc

@frappe.whitelist()
def material_request_item_query(doctype, txt, searchfield, start, page_len, filters, as_dict=False):
	"""Item lookup for Material Request items: allows both stock items
	and fixed asset items when request type is Material Issue / Material Transfer."""

	conditions = []

	if filters and filters.get("item_group"):
		conditions.append("i.item_group = %(item_group)s" % {"item_group": frappe.db.escape(filters.get("item_group"))})

	return frappe.db.sql(
		"""
		select
			i.name, i.item_name, i.item_group, i.stock_uom
		from
			`tabItem` i
		where
			i.disabled = 0
			and (i.is_stock_item = 1 or i.is_fixed_asset = 1)
			and (i.name like %(txt)s or i.item_name like %(txt)s)
			{conditions}
			{match_cond}
		order by
			if(locate(%(_txt)s, i.name), locate(%(_txt)s, i.name), 99999),
			i.idx desc,
			i.name asc
		limit %(page_len)s offset %(start)s
		""".format(
			conditions=(" and " + " and ".join(conditions)) if conditions else "",
			match_cond=get_match_cond(doctype),
		),
		{
			"txt": "%%%s%%" % txt,
			"_txt": txt.replace("%", ""),
			"start": start,
			"page_len": page_len,
		},
		as_dict=as_dict,
	)