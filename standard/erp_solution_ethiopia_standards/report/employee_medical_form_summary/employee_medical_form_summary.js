frappe.query_reports["Employee Medical Form Summary"] = {
    filters: [
        {
            fieldname: "view",
            label: "View",
            fieldtype: "Select",
            options: ["Detail", "Summary"],
            default: "Detail",
            reqd: 1
        },
        {
            fieldname: "group_by",
            label: "Group By (Summary only)",
            fieldtype: "Select",
            options: ["Reason", "Project", "Budget Year", "Type of Employee", "Injury Type", "Facility Type"],
            default: "Reason",
            depends_on: "eval:doc.view == 'Summary'"
        },
        {
            fieldname: "from_date",
            label: "From Date",
            fieldtype: "Date"
        },
        {
            fieldname: "to_date",
            label: "To Date",
            fieldtype: "Date"
        },
        {
            fieldname: "project",
            label: "Project",
            fieldtype: "Link",
            options: "Project"
        },
		{
    fieldname: "budget_year",
    label: "Budget Year",
    fieldtype: "Link",
    options: "Budget Year"
},
        {
            fieldname: "employee_id",
            label: "Employee",
            fieldtype: "Link",
            options: "Employee"
        },
        {
            fieldname: "gender",
            label: "Gender",
            fieldtype: "Link",
            options: "Gender"
        },
        {
            fieldname: "type_of_injury",
            label: "Type of Injury",
            fieldtype: "Select",
            options: ["", "ከስራ ጋር ያልተያያዘ ጉዳት", "የስራ ላይ ጉዳት"]
        },
        {
            fieldname: "type_of_employee",
            label: "Type of Employee",
            fieldtype: "Select",
            options: ["", "ለሰራተኛ", "ለስራ መሪ", "ለስራ አስፈፃሚ"]
        },
        {
            fieldname: "injury_type",
            label: "Injury Type",
            fieldtype: "Select",
            options: ["", "በጉዳቱ ምክንያት የወጣው ወጭ", "ሞት", "ቋሚ የአካል ጉዳት", "ከፊል የአካል ጉዳት"]
        },
        {
            fieldname: "reason",
            label: "Reason",
            fieldtype: "Select",
            options: [
                "", "ጠቅላላ ህክምና ለሰራተኛ", "ጠቅላላ ህክምና ለስራ መሪ", "ጠቅላላ ህክምና ለስራ አስፈፃሚ",
                "የመነፅር", "የመነጸር ሌንሥ", "የጆሮ ማዳመጫ", "የህክምና ለቤተሰብ",
                "የወሊድ", "ፊዚዮ ቴራፒ", "ለኩላሊት እጥበት", "ለልብ ህመም"
            ]
        },
        {
            fieldname: "facility_type",
            label: "Facility Type",
            fieldtype: "Select",
            options: ["", "የመንግስት", "የግል"]
        }
    ]
};