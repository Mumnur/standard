frappe.query_reports["Asset Report"] = {
	"filters": [
		{
			"fieldname": "company",
			"label": "Company",
			"fieldtype": "Link",
			"options": "Company",
			"default": frappe.defaults.get_user_default("Company")
		},
		{
			"fieldname": "from_date",
			"label": "Period End Date (From)",
			"fieldtype": "Date",
			"default": frappe.datetime.month_start(),
			"reqd": 1
		},
		{
			"fieldname": "to_date",
			"label": "Period End Date (To)",
			"fieldtype": "Date",
			"default": frappe.datetime.month_end(),
			"reqd": 1
		},
		{
			"fieldname": "asset_category",
			"label": "Asset Category",
			"fieldtype": "Link",
			"options": "Asset Category"
		},
		{
			"fieldname": "asset",
			"label": "Asset",
			"fieldtype": "Link",
			"options": "Asset"
		},
		{
			"fieldname": "item_code",
			"label": "Item Code",
			"fieldtype": "Link",
			"options": "Item"
		},
		{
			"fieldname": "status",
			"label": "Status",
			"fieldtype": "Select",
			"options": "\nDraft\nSubmitted\nPartially Depreciated\nFully Depreciated\nSold\nScrapped\nCapitalized"
		},
		{
			"fieldname": "custom_condition_rating",
			"label": "Condition Rating",
			"fieldtype": "Data"
		},
		{
			"fieldname": "location",
			"label": "Location",
			"fieldtype": "Link",
			"options": "Location"
		},
		{
			"fieldname": "department",
			"label": "Department",
			"fieldtype": "Link",
			"options": "Department"
		},
		{
			"fieldname": "cost_center",
			"label": "Cost Center",
			"fieldtype": "Link",
			"options": "Cost Center"
		},
		{
			"fieldname": "only_with_depreciation_in_period",
			"label": "Only Assets Depreciated in Period",
			"fieldtype": "Select",
			"options": "\nYes\nNo",
			"default": ""
		}
	],

	"formatter": function (value, row, column, data, default_formatter) {
		value = default_formatter(value, row, column, data);

		if (column.fieldname == "depreciation_percentage" && data) {
			if (flt(data.depreciation_percentage) >= 99.99) {
				value = `<span style="color:#e03131;font-weight:600">${value}</span>`;
			} else if (flt(data.depreciation_percentage) >= 75) {
				value = `<span style="color:#f08c00">${value}</span>`;
			}
		}

		if (column.fieldname == "period_depreciation_amount" && data) {
			if (flt(data.period_depreciation_amount) > 0) {
				value = `<span style="color:#2b8a3e;font-weight:600">${value}</span>`;
			} else {
				value = `<span style="color:#adb5bd">${value}</span>`;
			}
		}

		if (column.fieldname == "status" && data) {
			let colors = {
				"Submitted": "blue",
				"Draft": "grey",
				"Partially Depreciated": "orange",
				"Fully Depreciated": "red",
				"Capitalized": "green",
				"Sold": "purple",
				"Scrapped": "darkgrey"
			};
			let color = colors[data.status] || "grey";
			value = `<span class="indicator-pill ${color}" style="padding:2px 8px;border-radius:10px;">${data.status}</span>`;
		}

		return value;
	},

	"onload": function (report) {
		report.page.add_inner_button(__("Refresh"), function () {
			report.refresh();
		});
	}
};