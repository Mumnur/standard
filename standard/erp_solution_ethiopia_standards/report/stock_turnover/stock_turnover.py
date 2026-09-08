import frappe
from frappe import _

from erpnext.stock.report.stock_balance.stock_balance import StockBalanceReport


def execute(filters=None):

    filters = frappe._dict(filters or {})

    # ---------------------------------------------------------
    # Filters
    # ---------------------------------------------------------

    filters.report_type = filters.get("report_type") or "Company"

    filters.company = filters.get("company")
    filters.from_date = filters.get("from_date")
    filters.to_date = filters.get("to_date")

    filters.item_group = filters.get("item_group")
    filters.item_code = filters.get("item_code")
    filters.warehouse = filters.get("warehouse")

    filters.warehouse_type = None
    filters.include_uom = None

    filters.show_stock_ageing_data = False
    filters.show_variant_attributes = False
    filters.show_alt_uom_balance = False
    filters.include_zero_stock_items = False
    filters.show_dimension_wise_stock = False
    filters.ignore_closing_balance = False
    filters.valuation_field_type = "Currency"

    # ---------------------------------------------------------
    # Turnover Range
    #
    # Example:
    #
    # 2, 4
    #
    # 0 - 2     = Low
    # 2 - 4     = Normal
    # 4+        = High
    #
    # Example:
    #
    # 1, 3, 6
    #
    # 0 - 1     = Very Low
    # 1 - 3     = Low
    # 3 - 6     = Normal
    # 6+        = High
    # ---------------------------------------------------------

    range_string = filters.get("range") or "2, 4"

    turnover_ranges = []

    try:

        turnover_ranges = sorted(
            [
                frappe.utils.flt(value.strip())
                for value in str(range_string).split(",")
                if value.strip() != ""
            ]
        )

        # Remove negative values
        turnover_ranges = [
            value
            for value in turnover_ranges
            if value >= 0
        ]

    except Exception:

        turnover_ranges = [2.0, 4.0]

    # If invalid/empty range is supplied
    if not turnover_ranges:

        turnover_ranges = [2.0, 4.0]

    # Remove duplicates
    turnover_ranges = sorted(
        list(set(turnover_ranges))
    )

    # ---------------------------------------------------------
    # Company mode = all warehouses
    # ---------------------------------------------------------

    if filters.report_type == "Company":

        filters.warehouse = None

    # ---------------------------------------------------------
    # Run ERPNext Stock Balance
    # ---------------------------------------------------------

    stock_balance_report = StockBalanceReport(filters)

    stock_balance_columns, stock_balance_data = (
        stock_balance_report.run()
    )

    # ---------------------------------------------------------
    # Number of days in selected period
    # ---------------------------------------------------------

    from_date = frappe.utils.getdate(
        filters.from_date
    )

    to_date = frappe.utils.getdate(
        filters.to_date
    )

    period_days = (
        frappe.utils.date_diff(
            to_date,
            from_date
        ) + 1
    )

    if period_days <= 0:

        period_days = 1

    # ---------------------------------------------------------
    # Aggregate Stock Balance
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

                "item_group":
                    row.get("item_group"),

                "item_code":
                    item_code,

                "item_name":
                    row.get("item_name"),

                "stock_uom":
                    row.get("stock_uom"),

                "warehouse":
                    row.get("warehouse") or "",

                "opening_value":
                    0.0,

                "in_value":
                    0.0,

                "out_value":
                    0.0,

                "balance_value":
                    0.0
            }

        aggregated[key]["opening_value"] += (
            frappe.utils.flt(
                row.get("opening_val")
            )
        )

        aggregated[key]["in_value"] += (
            frappe.utils.flt(
                row.get("in_val")
            )
        )

        aggregated[key]["out_value"] += (
            frappe.utils.flt(
                row.get("out_val")
            )
        )

        aggregated[key]["balance_value"] += (
            frappe.utils.flt(
                row.get("bal_val")
            )
        )

    # ---------------------------------------------------------
    # Prepare final data
    # ---------------------------------------------------------

    data = []

    for row in aggregated.values():

        opening_value = frappe.utils.flt(
            row["opening_value"]
        )

        closing_value = frappe.utils.flt(
            row["balance_value"]
        )

        in_value = frappe.utils.flt(
            row["in_value"]
        )

        out_value = frappe.utils.flt(
            row["out_value"]
        )

        # -----------------------------------------------------
        # Average Inventory Value
        # -----------------------------------------------------

        average_stock_value = (
            opening_value +
            closing_value
        ) / 2

        # -----------------------------------------------------
        # Stock Turnover Ratio
        #
        # Turnover Ratio =
        #
        # Out Value / Average Inventory Value
        # -----------------------------------------------------

        if average_stock_value > 0:

            turnover_ratio = (
                out_value /
                average_stock_value
            )

        else:

            turnover_ratio = 0.0

        # -----------------------------------------------------
        # DIO
        #
        # DIO =
        #
        # Period Days / Turnover Ratio
        # -----------------------------------------------------

        if turnover_ratio > 0:

            dio = (
                period_days /
                turnover_ratio
            )

        else:

            dio = 0.0

        # -----------------------------------------------------
        # Dynamic Turnover Classification
        #
        # Uses the "range" filter.
        #
        # Example:
        #
        # range = "2, 4"
        #
        # < 2       Low
        # 2 - < 4   Normal
        # >= 4      High
        # -----------------------------------------------------

        if turnover_ratio <= 0:

            turnover_level = "No Movement"

            interpretation = (
                "No stock issued during the period"
            )

        elif len(turnover_ranges) == 1:

            # -----------------------------------------------
            # One threshold
            # -----------------------------------------------

            if turnover_ratio < turnover_ranges[0]:

                turnover_level = "Low"

                interpretation = (
                    "Slow moving inventory"
                )

            else:

                turnover_level = "High"

                interpretation = (
                    "Fast moving inventory"
                )

        elif len(turnover_ranges) == 2:

            # -----------------------------------------------
            # Two thresholds
            #
            # < first     Low
            # first-second Normal
            # >= second   High
            # -----------------------------------------------

            if turnover_ratio < turnover_ranges[0]:

                turnover_level = "Low"

                interpretation = (
                    "Slow moving inventory"
                )

            elif turnover_ratio < turnover_ranges[1]:

                turnover_level = "Normal"

                interpretation = (
                    "Normal inventory movement"
                )

            else:

                turnover_level = "High"

                interpretation = (
                    "Fast moving inventory"
                )

        else:

            # -----------------------------------------------
            # Three or more thresholds
            #
            # Example:
            #
            # 1, 3, 6
            #
            # < 1       Very Low
            # 1 - < 3   Low
            # 3 - < 6   Normal
            # >= 6      High
            # -----------------------------------------------

            if turnover_ratio < turnover_ranges[0]:

                turnover_level = "Very Low"

                interpretation = (
                    "Very slow moving inventory"
                )

            elif turnover_ratio < turnover_ranges[1]:

                turnover_level = "Low"

                interpretation = (
                    "Slow moving inventory"
                )

            elif turnover_ratio < turnover_ranges[2]:

                turnover_level = "Normal"

                interpretation = (
                    "Normal inventory movement"
                )

            else:

                turnover_level = "High"

                interpretation = (
                    "Fast moving inventory"
                )

        # -----------------------------------------------------
        # Append row
        # -----------------------------------------------------

        data.append({

            "item_group":
                row["item_group"],

            "item_code":
                row["item_code"],

            "item_name":
                row["item_name"],

            "stock_uom":
                row["stock_uom"],

            "warehouse":
                row["warehouse"],

            "opening_value":
                opening_value,

            "in_value":
                in_value,

            "out_value":
                out_value,

            "balance_value":
                closing_value,

            "average_stock_value":
                average_stock_value,

            "turnover_ratio":
                turnover_ratio,

            "dio":
                dio,

            "turnover_level":
                turnover_level,

            "interpretation":
                interpretation
        })

    # ---------------------------------------------------------
    # Turnover Level Filter
    # ---------------------------------------------------------

    turnover_level_filter = filters.get(
        "turnover_level"
    )

    if (
        turnover_level_filter
        and turnover_level_filter != "All"
    ):

        data = [

            row
            for row in data
            if row.get("turnover_level")
            == turnover_level_filter

        ]

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

    # ---------------------------------------------------------
    # Warehouse
    # ---------------------------------------------------------

    if filters.report_type == "By Project":

        columns.append({

            "fieldname": "warehouse",

            "label": _("Project / Warehouse"),

            "fieldtype": "Link",

            "options": "Warehouse",

            "width": 220
        })

    # ---------------------------------------------------------
    # Value Columns
    # ---------------------------------------------------------

    columns.extend([

        {
            "fieldname": "opening_value",
            "label": _("Opening Value"),
            "fieldtype": "Currency",
            "options": "Company:company:default_currency",
            "width": 140
        },

        {
            "fieldname": "in_value",
            "label": _("In Value"),
            "fieldtype": "Currency",
            "options": "Company:company:default_currency",
            "width": 140
        },

        {
            "fieldname": "out_value",
            "label": _("Out Value"),
            "fieldtype": "Currency",
            "options": "Company:company:default_currency",
            "width": 140
        },

        {
            "fieldname": "balance_value",
            "label": _("Closing Value"),
            "fieldtype": "Currency",
            "options": "Company:company:default_currency",
            "width": 140
        },

        {
            "fieldname": "average_stock_value",
            "label": _("Average Stock Value"),
            "fieldtype": "Currency",
            "options": "Company:company:default_currency",
            "width": 160
        },

        {
            "fieldname": "turnover_ratio",
            "label": _("Stock Turnover Ratio"),
            "fieldtype": "Float",
            "precision": 2,
            "width": 160
        },

        {
            "fieldname": "dio",
            "label": _("DIO (Days)"),
            "fieldtype": "Float",
            "precision": 1,
            "width": 120
        },

        {
            "fieldname": "turnover_level",
            "label": _("Turnover Level"),
            "fieldtype": "Data",
            "width": 130
        },

        {
            "fieldname": "interpretation",
            "label": _("Interpretation"),
            "fieldtype": "Data",
            "width": 220
        }

    ])

    return columns, data