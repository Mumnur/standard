frappe.query_reports["Employee Relieving Report"] = {
	"filters": [

		// -----------------------------------------
		// Ethiopian From Relieving Date
		// -----------------------------------------
		{
			"fieldname": "from_relieving_date_ec",
			"label": __("From Relieving Date (E.C.)"),
			"fieldtype": "Data",

			change: function () {
				ConvertFromRelievingDate(frappe.query_report);
			},
		},

		// -----------------------------------------
		// Gregorian From Relieving Date
		// -----------------------------------------
		{
			"fieldname": "from_relieving_date",
			"label": __("From Relieving Date"),
			"fieldtype": "Date",
			"default": frappe.datetime.add_months(frappe.datetime.get_today(), -12)
		},

		// -----------------------------------------
		// Ethiopian To Relieving Date
		// -----------------------------------------
		{
			"fieldname": "to_relieving_date_ec",
			"label": __("To Relieving Date (E.C.)"),
			"fieldtype": "Data",

			change: function () {
				ConvertToRelievingDate(frappe.query_report);
			},
		},

		// -----------------------------------------
		// Gregorian To Relieving Date
		// -----------------------------------------
		{
			"fieldname": "to_relieving_date",
			"label": __("To Relieving Date"),
			"fieldtype": "Date",
			"default": frappe.datetime.get_today()
		},

		{
			"fieldname": "company",
			"label": __("Company"),
			"fieldtype": "Link",
			"options": "Company",
			"default": frappe.defaults.get_user_default("Company")
		},
		{
			"fieldname": "department",
			"label": __("Department"),
			"fieldtype": "Link",
			"options": "Department"
		},
		{
			"fieldname": "designation",
			"label": __("Designation"),
			"fieldtype": "Link",
			"options": "Designation"
		},
		{
			"fieldname": "branch",
			"label": __("Branch"),
			"fieldtype": "Link",
			"options": "Branch"
		},
		{
			"fieldname": "gender",
			"label": __("Gender"),
			"fieldtype": "Link",
			"options": "Gender"
		},
		{
			"fieldname": "custom_reason",
			"label": __("Reason for Leaving"),
			"fieldtype": "Link",
			"options": "Reason"
		}
	],

	onload: function (report) {

		// -----------------------------------------
		// Set Ethiopian From Relieving Date
		// -----------------------------------------

		const fromDate = report.get_filter_value("from_relieving_date");

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

		const toDate = report.get_filter_value("to_relieving_date");

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

	report.set_filter_value("from_relieving_date", gregorianDate);
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

	report.set_filter_value("to_relieving_date", gregorianDate);
}