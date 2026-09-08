frappe.ui.form.on("Biometric Attendance Import", {
    refresh(frm) {
        if (frm.is_new()) {
            return;
        }

        frm.add_custom_button(__("Parse File"), function () {
            frappe.call({
                method: "parse_file",
                doc: frm.doc,
                freeze: true,
                freeze_message: __("Reading biometric Excel file..."),
                callback: function (r) {
                    if (!r.exc) {
                        frm.reload_doc();
                    }
                }
            });
        });

        frm.add_custom_button(__("Create Draft Attendance"), function () {
            frappe.confirm(
                __("Create draft Attendance records from the reviewed rows?"),
                function () {
                    frappe.call({
                        method: "create_attendance",
                        doc: frm.doc,
                        freeze: true,
                        freeze_message: __("Creating Attendance records..."),
                        callback: function (r) {
                            if (!r.exc) {
                                frm.reload_doc();
                            }
                        }
                    });
                }
            );
        });
    }
});