# Copyright (c) 2026, Muhammed Nurhusien
# For license information, please see license.txt

import frappe
from frappe.utils import flt, getdate, nowdate, date_diff, add_months, get_first_day, get_last_day


def execute(filters=None):
    filters = filters or {}
    columns = get_columns()
    data = get_data(filters)
    chart = get_chart_data(data)
    summary = get_report_summary(data)
    return columns, data, None, chart, summary


# ---------------------------------------------------------------
# COLUMNS
# ---------------------------------------------------------------
def get_columns():
    return [
        {"label": "Asset", "fieldname": "name", "fieldtype": "Link", "options": "Asset", "width": 120},
        {"label": "Asset Name", "fieldname": "asset_name", "fieldtype": "Data", "width": 150},
        {"label": "Item Code", "fieldname": "item_code", "fieldtype": "Link", "options": "Item", "width": 110},
        {"label": "Item Name", "fieldname": "item_name", "fieldtype": "Data", "width": 130},
        {"label": "Category", "fieldname": "asset_category", "fieldtype": "Link", "options": "Asset Category", "width": 180},
        {"label": "Status", "fieldname": "status", "fieldtype": "Data", "width": 100},
        {"label": "Company", "fieldname": "company", "fieldtype": "Link", "options": "Company", "width": 120},
        {"label": "Location", "fieldname": "location", "fieldtype": "Link", "options": "Location", "width": 110},
        {"label": "Department", "fieldname": "department", "fieldtype": "Link", "options": "Department", "width": 110},
        {"label": "Cost Center", "fieldname": "cost_center", "fieldtype": "Link", "options": "Cost Center", "width": 120},
        {"label": "Condition Rating", "fieldname": "custom_condition_rating", "fieldtype": "Data", "width": 110},
        {"label": "Purchase Date", "fieldname": "purchase_date", "fieldtype": "Date", "width": 120},
        {"label": "Available For Use", "fieldname": "available_for_use_date", "fieldtype": "Date", "width": 120},
        {"label": "Gross Carrying Amount", "fieldname": "custom_gross_carrying_amount", "fieldtype": "Currency", "width": 140},
        {"label": "Residual Value Amount", "fieldname": "custom_residual_value_amount", "fieldtype": "Currency", "width": 130},
        {"label": "Depreciable Amount", "fieldname": "custom_depreciable_amount", "fieldtype": "Currency", "width": 130},
        {"label": "Monthly Depreciation", "fieldname": "custom_monthly_depreciation", "fieldtype": "Currency", "width": 130},
        {"label": "Periods in Range", "fieldname": "periods_in_range", "fieldtype": "Int", "width": 100},
        {"label": "Opening NBV (Period Start)", "fieldname": "period_opening_nbv", "fieldtype": "Currency", "width": 150},
        {"label": "Depreciation Amount (Period)", "fieldname": "period_depreciation_amount", "fieldtype": "Currency", "width": 160},
        {"label": "Closing NBV (Period End)", "fieldname": "period_closing_nbv", "fieldtype": "Currency", "width": 150},
        {"label": "Accumulated Depreciation (as on To Date)", "fieldname": "accumulated_depreciation", "fieldtype": "Currency", "width": 180},
        {"label": "Depreciation %", "fieldname": "depreciation_percentage", "fieldtype": "Percent", "width": 110},
        {"label": "Last Period End Date", "fieldname": "last_period_end_date", "fieldtype": "Date", "width": 130},
    ]


# ---------------------------------------------------------------
# DATA
# ---------------------------------------------------------------
def get_data(filters):
    from_date = filters.get("from_date") or get_first_day(nowdate())
    to_date = filters.get("to_date") or get_last_day(nowdate())

    conditions = get_conditions(filters)

    assets = frappe.db.sql(f"""
        SELECT
            a.name, a.item_code, a.item_name, a.asset_name, a.asset_category,
            a.status, a.company, a.location, a.department, a.cost_center,
            a.custom_condition_rating, a.custom_condition_,
            a.purchase_date, a.available_for_use_date,
            a.custom_use_full_life_basis_in_year, a.net_purchase_amount,
            a.custom_total_use_full_life_in_year, a.custom_gross_carrying_amount,
            a.custom_residual_value_, a.custom_residual_value_amount,
            a.custom_depreciable_amount, a.custom_useful_life,
            a.custom_monthly_depreciation
        FROM `tabAsset` a
        WHERE a.docstatus < 2 {conditions}
        ORDER BY a.asset_name ASC
    """, filters, as_dict=1)

    if not assets:
        return []

    asset_names = [a.name for a in assets]

    # ---- Schedule rows WITHIN the selected period (from_date - to_date) ----
    period_rows = frappe.db.sql("""
        SELECT parent, period_end_date, opening_nbv, depreciation_charge,
               closing_nbv, accumulated_depreciation
        FROM `tabAsset Monthly Depreciation Schedule`
        WHERE parent IN %(assets)s
          AND period_end_date BETWEEN %(from_date)s AND %(to_date)s
        ORDER BY parent, period_end_date ASC
    """, {"assets": asset_names, "from_date": from_date, "to_date": to_date}, as_dict=1)

    period_map = {}
    for row in period_rows:
        period_map.setdefault(row.parent, []).append(row)

    # ---- Latest schedule row up to "to_date" (for overall accumulated depreciation) ----
    upto_rows = frappe.db.sql("""
        SELECT parent, period_end_date, accumulated_depreciation
        FROM `tabAsset Monthly Depreciation Schedule`
        WHERE parent IN %(assets)s
          AND period_end_date <= %(to_date)s
        ORDER BY parent, period_end_date ASC
    """, {"assets": asset_names, "to_date": to_date}, as_dict=1)

    latest_upto = {}
    for row in upto_rows:
        latest_upto[row.parent] = row  # keeps overwriting -> last one wins (latest date)

    result = []

    for a in assets:
        rows = period_map.get(a.name, [])

        a.periods_in_range = len(rows)
        a.period_opening_nbv = flt(rows[0].opening_nbv) if rows else None
        a.period_closing_nbv = flt(rows[-1].closing_nbv) if rows else None
        a.period_depreciation_amount = sum(flt(r.depreciation_charge) for r in rows) if rows else 0
        a.last_period_end_date = rows[-1].period_end_date if rows else None

        upto = latest_upto.get(a.name)
        a.accumulated_depreciation = flt(upto.accumulated_depreciation) if upto else 0

        depreciable_amount = flt(a.custom_depreciable_amount)
        a.depreciation_percentage = (
            (a.accumulated_depreciation / depreciable_amount) * 100
            if depreciable_amount else 0
        )

        # Filter: only show assets that actually had depreciation in this period
        if filters.get("only_with_depreciation_in_period") == "Yes" and not rows:
            continue

        result.append(a)

    return result


def get_conditions(filters):
    conditions = ""

    if filters.get("company"):
        conditions += " AND a.company = %(company)s"

    if filters.get("asset_category"):
        conditions += " AND a.asset_category = %(asset_category)s"

    if filters.get("item_code"):
        conditions += " AND a.item_code = %(item_code)s"

    if filters.get("status"):
        conditions += " AND a.status = %(status)s"

    if filters.get("location"):
        conditions += " AND a.location = %(location)s"

    if filters.get("department"):
        conditions += " AND a.department = %(department)s"

    if filters.get("cost_center"):
        conditions += " AND a.cost_center = %(cost_center)s"

    if filters.get("custom_condition_rating"):
        conditions += " AND a.custom_condition_rating = %(custom_condition_rating)s"

    if filters.get("asset"):
        conditions += " AND a.name = %(asset)s"

    return conditions


# ---------------------------------------------------------------
# CHART — Depreciation amount for the period, grouped by category
# ---------------------------------------------------------------
def get_chart_data(data):
    if not data:
        return None

    category_totals = {}

    for row in data:
        cat = row.get("asset_category") or "Uncategorized"
        if cat not in category_totals:
            category_totals[cat] = {"period_dep": 0, "accum_dep": 0, "nbv": 0}
        category_totals[cat]["period_dep"] += flt(row.get("period_depreciation_amount"))
        category_totals[cat]["accum_dep"] += flt(row.get("accumulated_depreciation"))
        category_totals[cat]["nbv"] += flt(row.get("period_closing_nbv"))

    labels = list(category_totals.keys())

    return {
        "data": {
            "labels": labels,
            "datasets": [
                {"name": "Depreciation Amount (Period)", "values": [category_totals[l]["period_dep"] for l in labels]},
                {"name": "Accumulated Depreciation (as on To Date)", "values": [category_totals[l]["accum_dep"] for l in labels]},
                {"name": "Closing NBV (Period End)", "values": [category_totals[l]["nbv"] for l in labels]},
            ],
        },
        "type": "bar",
        "barOptions": {"stacked": 0},
        "colors": ["#ff5858", "#f08c00", "#28a745"],
    }


# ---------------------------------------------------------------
# SUMMARY CARDS
# ---------------------------------------------------------------
def get_report_summary(data):
    if not data:
        return []

    total_assets = len(data)
    total_period_dep = sum(flt(d.get("period_depreciation_amount")) for d in data)
    total_accum_dep = sum(flt(d.get("accumulated_depreciation")) for d in data)
    total_closing_nbv = sum(flt(d.get("period_closing_nbv")) for d in data if d.get("period_closing_nbv") is not None)
    assets_with_dep = len([d for d in data if flt(d.get("period_depreciation_amount")) > 0])

    return [
        {"value": total_assets, "label": "Total Assets", "datatype": "Int", "indicator": "blue"},
        {"value": assets_with_dep, "label": "Assets Depreciated in Period", "datatype": "Int", "indicator": "orange"},
        {"value": total_period_dep, "label": "Total Depreciation (Period)", "datatype": "Currency", "indicator": "red"},
        {"value": total_accum_dep, "label": "Total Accumulated Depreciation (as on To Date)", "datatype": "Currency", "indicator": "orange"},
        {"value": total_closing_nbv, "label": "Total Closing NBV (Period End)", "datatype": "Currency", "indicator": "green"},
    ]