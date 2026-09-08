frappe.query_reports["Employee Current Education"] = {
      "filters": [
        
        {
	   "fieldname":"level",
	   "label": __("Education Level"),
	   "fieldtype": "Link",
	   "options": "Education Level"
	},
	{
	   "fieldname":"employeement_type",
	   "label": __("Employeement Type"),
	   "fieldtype": "Link",
	   "options": "Employment Type"
	}
    ]
};


