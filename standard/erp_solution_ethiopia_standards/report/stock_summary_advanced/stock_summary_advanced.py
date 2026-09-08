import frappe
from frappe import _

from erpnext.stock.report.stock_balance.stock_balance import StockBalanceReport


def execute(filters=None):
    filters = frappe._dict(filters or {})

    # ---------------------------------------------------------
    # Default filters
    # ---------------------------------------------------------

    filters.report_type = filters.get("report_type") or "Company"

    filters.company = filters.get("company")
    filters.from_date = filters.get("from_date")
    filters.to_date = filters.get("to_date")

    filters.item_group = filters.get("item_group")

    # ---------------------------------------------------------
    # IMPORTANT:
    # ERPNext v16 Stock Balance expects item_code as a LIST
    # ---------------------------------------------------------

    item_code = filters.get("item_code")

    if item_code:
        if isinstance(item_code, str):
            filters.item_code = [item_code]
        else:
            filters.item_code = item_code
    else:
        filters.item_code = None

    # ---------------------------------------------------------
    # IMPORTANT:
    # ERPNext v16 Stock Balance expects warehouse as a LIST
    # ---------------------------------------------------------

    warehouse = filters.get("warehouse")

    if warehouse:
        if isinstance(warehouse, str):
            filters.warehouse = [warehouse]
        else:
            filters.warehouse = warehouse
    else:
        filters.warehouse = None

    filters.warehouse_type = filters.get("warehouse_type")
    filters.include_uom = filters.get("include_uom")

    filters.show_stock_ageing_data = False
    filters.show_variant_attributes = False
    filters.show_alt_uom_balance = False
    filters.include_zero_stock_items = False
    filters.show_dimension_wise_stock = False
    filters.ignore_closing_balance = False
    filters.valuation_field_type = "Currency"

    # ---------------------------------------------------------
    # Company mode = all warehouses
    # ---------------------------------------------------------

    if filters.report_type == "Company":
        filters.warehouse = None

    # ---------------------------------------------------------
    # Run ERPNext v16 Stock Balance
    # ---------------------------------------------------------

    stock_balance_report = StockBalanceReport(filters)

    stock_balance_columns, stock_balance_data = stock_balance_report.run()

    # ---------------------------------------------------------
    # Aggregate ERPNext Stock Balance result
    # ---------------------------------------------------------

    aggregated = {}

    for row in stock_balance_data:

        item_code = row.get("item_code")

        if not item_code:
            continue

        if filters.report_type == "Company":
            key = item_code
        else:
            key = (
                item_code,
                row.get("warehouse") or ""
            )

        if key not in aggregated:

            aggregated[key] = {
                "item_group": row.get("item_group"),
                "item_code": item_code,
                "item_name": row.get("item_name"),
                "stock_uom": row.get("stock_uom"),
                "warehouse": row.get("warehouse") or "",

                "opening_qty": 0.0,
                "in_qty": 0.0,
                "out_qty": 0.0,
                "bal_qty": 0.0,

                "opening_val": 0.0,
                "in_val": 0.0,
                "out_val": 0.0,
                "bal_val": 0.0
            }

        aggregated[key]["opening_qty"] += frappe.utils.flt(
            row.get("opening_qty")
        )

        aggregated[key]["in_qty"] += frappe.utils.flt(
            row.get("in_qty")
        )

        aggregated[key]["out_qty"] += frappe.utils.flt(
            row.get("out_qty")
        )

        aggregated[key]["bal_qty"] += frappe.utils.flt(
            row.get("bal_qty")
        )

        aggregated[key]["opening_val"] += frappe.utils.flt(
            row.get("opening_val")
        )

        aggregated[key]["in_val"] += frappe.utils.flt(
            row.get("in_val")
        )

        aggregated[key]["out_val"] += frappe.utils.flt(
            row.get("out_val")
        )

        aggregated[key]["bal_val"] += frappe.utils.flt(
            row.get("bal_val")
        )

    # ---------------------------------------------------------
    # Final data
    # ---------------------------------------------------------

    data = []

    for row in aggregated.values():

        data.append({
            "item_group": row["item_group"],
            "item_code": row["item_code"],
            "item_name": row["item_name"],
            "stock_uom": row["stock_uom"],
            "warehouse": row["warehouse"],

            "opening_qty": row["opening_qty"],
            "in_qty": row["in_qty"],
            "out_qty": row["out_qty"],
            "bal_qty": row["bal_qty"],

            "opening_val": row["opening_val"],
            "in_val": row["in_val"],
            "out_val": row["out_val"],
            "bal_val": row["bal_val"]
        })

    # ---------------------------------------------------------
    # Sort
    # ---------------------------------------------------------

    data = sorted(
        data,
        key=lambda x: (
            x.get("item_group") or "",
            x.get("item_code") or "",
            x.get("warehouse") or ""
        )
    )

    # ---------------------------------------------------------
    # Columns
    # ---------------------------------------------------------

    columns = [

        {
            "fieldname": "item_group",
            "label": _("Item Group"),
            "fieldtype": "Link",
            "options": "Item Group",
            "width": 180
        },

        {
            "fieldname": "item_code",
            "label": _("Item Code"),
            "fieldtype": "Link",
            "options": "Item",
            "width": 150
        },

        {
            "fieldname": "item_name",
            "label": _("Item Name"),
            "fieldtype": "Data",
            "width": 220
        },

        {
            "fieldname": "stock_uom",
            "label": _("UOM"),
            "fieldtype": "Link",
            "options": "UOM",
            "width": 100
        }
    ]

    if filters.report_type == "By Project":

        columns.append({
            "fieldname": "warehouse",
            "label": _("Project / Warehouse"),
            "fieldtype": "Link",
            "options": "Warehouse",
            "width": 220
        })

    # ---------------------------------------------------------
    # Quantity or Value
    # ---------------------------------------------------------

    if filters.get("value_or_qty") == "Value":

        columns.extend([

            {
                "fieldname": "opening_val",
                "label": _("Opening Value"),
                "fieldtype": "Currency",
                "width": 140
            },

            {
                "fieldname": "in_val",
                "label": _("In Value"),
                "fieldtype": "Currency",
                "width": 140
            },

            {
                "fieldname": "out_val",
                "label": _("Out Value"),
                "fieldtype": "Currency",
                "width": 140
            },

            {
                "fieldname": "bal_val",
                "label": _("Balance Value"),
                "fieldtype": "Currency",
                "width": 140
            }

        ])

    else:

        columns.extend([

            {
                "fieldname": "opening_qty",
                "label": _("Opening Qty"),
                "fieldtype": "Float",
                "width": 130
            },

            {
                "fieldname": "in_qty",
                "label": _("In Qty"),
                "fieldtype": "Float",
                "width": 130
            },

            {
                "fieldname": "out_qty",
                "label": _("Out Qty"),
                "fieldtype": "Float",
                "width": 130
            },

            {
                "fieldname": "bal_qty",
                "label": _("Balance Qty"),
                "fieldtype": "Float",
                "width": 130
            }

        ])

    return columns, data