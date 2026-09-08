// Copyright (c) 2026, ERP Solution Ethiopia PLC and contributors
// For license information, please see license.txt

/* ------------------------------------------------------------------ *
 *  Ethiopian <-> Gregorian calendar conversion (Julian Day Number)
 *  Standard proleptic conversion, Amete Mihret epoch.
 *  NOTE: This block must stay at the top of the file — the filter
 *  defaults below call toEC() at load time, before the object literal
 *  is even built, so these must already be initialized by then.
 * ------------------------------------------------------------------ */

const JD_EPOCH_OFFSET_AMETE_MIHRET = 1723856;

function ethiopicToJDN(year, month, day) {
	return day + (month - 1) * 30 + (year - 1) * 365 + Math.floor(year / 4) + JD_EPOCH_OFFSET_AMETE_MIHRET - 1;
}

function jdnToEthiopic(jdn) {
	const r = (jdn - JD_EPOCH_OFFSET_AMETE_MIHRET) % 1461;
	const n = (r % 365) + 365 * Math.floor(r / 1460);
	const year =
		4 * Math.floor((jdn - JD_EPOCH_OFFSET_AMETE_MIHRET) / 1461) + Math.floor(r / 365) - Math.floor(r / 1460);
	const month = Math.floor(n / 30) + 1;
	const day = (n % 30) + 1;
	return [year, month, day];
}

function gregorianToJDN(year, month, day) {
	const a = Math.floor((month - 14) / 12);
	return (
		Math.floor((1461 * (year + 4800 + a)) / 4) +
		Math.floor((367 * (month - 2 - 12 * a)) / 12) -
		Math.floor((3 * Math.floor((year + 4900 + a) / 100)) / 4) +
		day -
		32075
	);
}

function jdnToGregorian(jdn) {
	const a = jdn + 32044;
	const b = Math.floor((4 * a + 3) / 146097);
	const c = a - Math.floor((146097 * b) / 4);
	const d = Math.floor((4 * c + 3) / 1461);
	const e = c - Math.floor((1461 * d) / 4);
	const m = Math.floor((5 * e + 2) / 153);
	const day = e - Math.floor((153 * m + 2) / 5) + 1;
	const month = m + 3 - 12 * Math.floor(m / 10);
	const year = 100 * b + d - 4800 + Math.floor(m / 10);
	return [year, month, day];
}

function toEC(gcArray) {
	const [year, month, day] = gcArray;
	return jdnToEthiopic(gregorianToJDN(year, month, day));
}

function toGC(ecArray) {
	const [year, month, day] = ecArray;
	return jdnToGregorian(ethiopicToJDN(year, month, day));
}

/* ------------------------------------------------------------------ *
 *  Report definition
 * ------------------------------------------------------------------ */

let syncingDates = false; // guards against the GC<->EC round-trip feedback loop

// Compute EC defaults up front so the EC filters are populated the moment
// the filter panel renders — no dependency on onload timing or filter order.
const defaultToDateGC = frappe.datetime.get_today();
const defaultFromDateGC = frappe.datetime.add_months(defaultToDateGC, -12); // last year -> today

function gcStringToEcString(gcDateStr) {
	const [y, m, d] = toEC(gcDateStr.split("-").map(Number));
	return `${d.toString().padStart(2, "0")}/${m.toString().padStart(2, "0")}/${y}`;
}

frappe.query_reports["Human Resource Informations"] = {
	"filters": [
		{
			"fieldname": "employee_status",
			"label": __("Employee Status"),
			"fieldtype": "Select",
			"options": ["All Employee", "Active Employee", "Left Employee"],
			"default": "All Employee",
			"reqd": 1,
			"change": function () {
				updateDateFilterLabels(frappe.query_report);
			},
		},
		{
			"fieldname": "ec_from_date_ec",
			"label": __("From Date (E.C.)"),
			"fieldtype": "Data",
			"reqd": 1,
			"default": gcStringToEcString(defaultFromDateGC),
			"change": function () { ConvertFromDate(frappe.query_report); },
		},
		{
			"fieldname": "ec_to_date_ec",
			"label": __("To Date (E.C.)"),
			"fieldtype": "Data",
			"reqd": 1,
			"default": gcStringToEcString(defaultToDateGC),
			"change": function () { ConvertToDate(frappe.query_report); },
		},
		{
			"fieldname": "from_date",
			"label": __("From Date"),
			"fieldtype": "Date",
			"width": "80",
			"reqd": 1,
			"default": defaultFromDateGC,
		},
	
		{
			"fieldname": "to_date",
			"label": __("To Date"),
			"fieldtype": "Date",
			"width": "80",
			"reqd": 1,
			"default": defaultToDateGC,
		},
	
		{
			"fieldname": "company",
			"label": __("Company"),
			"fieldtype": "Link",
			"options": "Company",
			"default": frappe.defaults.get_user_default("Company"),
		},
		{
			"fieldname": "branch",
			"label": __("Company Branch"),
			"fieldtype": "Link",
			"options": "Company Branch",
		},
		{
			"fieldname": "department",
			"label": __("Department"),
			"fieldtype": "Link",
			"options": "Department",
			"get_query": function () {
				var company = frappe.query_report.get_filter_value("company");
				return { filters: { company: company } };
			},
		},
		{
			"fieldname": "designation",
			"label": __("Designation"),
			"fieldtype": "Link",
			"options": "Designation",
		},
		{
			"fieldname": "employment_type",
			"label": __("Employment Type"),
			"fieldtype": "Link",
			"options": "Employment Type",
		},
		{
			"fieldname": "project",
			"label": __("Project"),
			"fieldtype": "Link",
			"options": "Project",
		},
		{
			"fieldname": "grade",
			"label": __("Grade"),
			"fieldtype": "Link",
			"options": "Employee Grade",
		},
		{
			"fieldname": "gender",
			"label": __("Gender"),
			"fieldtype": "Link",
			"options": "Gender",
		},
		{
			"fieldname": "status",
			"label": __("Status"),
			"fieldtype": "Select",
			"options": ["", "Active", "Inactive", "Suspended", "Left"],
		},
	],

	formatter: function (value, row, column, data, default_formatter) {
		value = default_formatter(value, row, column, data);
		if (column.fieldname === "age" && data && data.age !== undefined && data.age !== null) {
			value = `<span style="color: green; font-weight: 600;">${data.age}</span>`;
		}
		return value;
	},

	onload: function (report) {
		// Defaults already cover the initial EC values now. This just keeps
		// GC and EC in sync if something else (e.g. a saved filter set,
		// or a future change) updates from_date/to_date without going
		// through ConvertFromDate/ConvertToDate first.
		syncFromGCtoEC(report);
		updateDateFilterLabels(report);

		// Forces a clean run now that all reqd filters (including the EC
		// ones) are guaranteed to have values.
		report.refresh();
	},
};

/* Converts current from_date/to_date (GC) into the EC filters, guarded
 * so it doesn't trigger ConvertFromDate/ConvertToDate and bounce back. */
function syncFromGCtoEC(report) {
	syncingDates = true;

	const fromDate = report.get_filter_value("from_date");
	const toDate = report.get_filter_value("to_date");

	if (fromDate) {
		report.set_filter_value("ec_from_date_ec", gcStringToEcString(fromDate));
	}
	if (toDate) {
		report.set_filter_value("ec_to_date_ec", gcStringToEcString(toDate));
	}

	syncingDates = false;
}

function ConvertFromDate(report) {
	if (syncingDates) return; // skip when triggered programmatically, not by the user

	const ecDate = report.get_filter_value("ec_from_date_ec");
	if (ecDate) {
		const [day, month, year] = ecDate.split("/").map(Number);
		const [y, m, d] = toGC([year, month, day]);
		report.set_filter_value("from_date", `${y}-${String(m).padStart(2, "0")}-${String(d).padStart(2, "0")}`);
	}
}

function ConvertToDate(report) {
	if (syncingDates) return;

	const ecDate = report.get_filter_value("ec_to_date_ec");
	if (ecDate) {
		const [day, month, year] = ecDate.split("/").map(Number);
		const [y, m, d] = toGC([year, month, day]);
		report.set_filter_value("to_date", `${y}-${String(m).padStart(2, "0")}-${String(d).padStart(2, "0")}`);
	}
}

/* Relabels the date filters so users know whether the range applies to
 * Joining Date or Relieving Date, based on the Employee Status filter. */
function updateDateFilterLabels(report) {
	const employeeStatus = report.get_filter_value("employee_status");
	const isLeft = employeeStatus === "Left Employee";

	const labels = {
		from_date: isLeft ? __("From Date (Relieving)") : __("From Date (Joining)"),
		to_date: isLeft ? __("To Date (Relieving)") : __("To Date (Joining)"),
		ec_from_date_ec: isLeft ? __("From Date (Relieving) (E.C.)") : __("From Date (Joining) (E.C.)"),
		ec_to_date_ec: isLeft ? __("To Date (Relieving) (E.C.)") : __("To Date (Joining) (E.C.)"),
	};

	Object.keys(labels).forEach(function (fieldname) {
		const filter = report.get_filter(fieldname);
		if (filter) {
			filter.df.label = labels[fieldname];
			filter.refresh();
		}
	});
}