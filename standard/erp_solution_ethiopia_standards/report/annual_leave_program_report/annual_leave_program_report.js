frappe.query_reports["Annual Leave Program Report"] = {
	"filters": [
		{
			"fieldname": "department",
			"label": __("Department"),
			"fieldtype": "Link",
			"options": "Department",
			"width": "100"
		},
		{
			"fieldname": "employee",
			"label": __("Employee"),
			"fieldtype": "Link",
			"options": "Employee",
			"width": "100"
		},
		{
			"fieldname": "project",
			"label": __("Project"),
			"fieldtype": "Link",
			"options": "Project",
			"width": "100"
		},
		{
			"fieldname": "budget_year",
			"label": __("Budget Year"),
			"fieldtype": "Link",
			"options": "Budget Year",
			"width": "100"
		},
		{
			"fieldname": "from_relieving_date_ec",
			"label": __("From Date (E.C.)"),
			"fieldtype": "Data",

			change: function () {
				ConvertFromRelievingDate(frappe.query_report);
			},
		},
		{
			"fieldname": "to_relieving_date_ec",
			"label": __("To Date (E.C.)"),
			"fieldtype": "Data",

			change: function () {
				ConvertToRelievingDate(frappe.query_report);
			},
		},

		{
			"fieldname": "from_date",
			"label": __("From Date"),
			"fieldtype": "Date",
			"default": frappe.datetime.add_months(frappe.datetime.get_today(), -1),
			"width": "80"
		},
		
		{
			"fieldname": "to_date",
			"label": __("To Date"),
			"fieldtype": "Date",
			"default": frappe.datetime.get_today(),
			"width": "80"
		},
		
	],
	onload: function (report) {

		// -----------------------------------------
		// Set Ethiopian From Relieving Date
		// -----------------------------------------

		const fromDate = report.get_filter_value("from_date");

		if (fromDate) {
			const [year, month, day] = toEC(
				fromDate.split("-").map(Number)
			);

			const ecDateFrom =
				`${String(day).padStart(2, "0")}/${String(month).padStart(2, "0")}/${year}`;

			report.set_filter_value("from_relieving_date_ec", ecDateFrom);
		}

		// -----------------------------------------
		// Set Ethiopian To Relieving Date
		// -----------------------------------------

		const toDate = report.get_filter_value("to_date");

		if (toDate) {
			const [year, month, day] = toEC(
				toDate.split("-").map(Number)
			);

			const ecDateTo =
				`${String(day).padStart(2, "0")}/${String(month).padStart(2, "0")}/${year}`;

			report.set_filter_value("to_relieving_date_ec", ecDateTo);
		}
	},
};

// =================================================
// Ethiopian From Relieving Date → Gregorian
// =================================================

function ConvertFromRelievingDate(report) {

	const ecDate = report.get_filter_value("from_relieving_date_ec");

	if (!ecDate) {
		return;
	}

	const [day, month, year] = ecDate.split("/").map(Number);

	const gcDate = toGC([year, month, day]);

	const gregorianDate =
		`${gcDate[0]}-${String(gcDate[1]).padStart(2, "0")}-${String(gcDate[2]).padStart(2, "0")}`;

	report.set_filter_value("from_date", gregorianDate);
}


// =================================================
// Ethiopian To Relieving Date → Gregorian
// =================================================

function ConvertToRelievingDate(report) {

	const ecDate = report.get_filter_value("to_relieving_date_ec");

	if (!ecDate) {
		return;
	}

	const [day, month, year] = ecDate.split("/").map(Number);

	const gcDate = toGC([year, month, day]);

	const gregorianDate =
		`${gcDate[0]}-${String(gcDate[1]).padStart(2, "0")}-${String(gcDate[2]).padStart(2, "0")}`;

	report.set_filter_value("to_date", gregorianDate);
}