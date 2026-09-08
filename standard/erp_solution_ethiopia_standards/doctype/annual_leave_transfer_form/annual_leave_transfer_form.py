import frappe
from frappe.model.document import Document


class AnnualLeaveTransferForm(Document):
    pass


@frappe.whitelist()
def get_current_leave_balance(employee, leave_type):
    from hrms.hr.doctype.leave_application.leave_application import get_leave_balance_on

    balance = get_leave_balance_on(
        employee=employee,
        leave_type=leave_type,
        date=frappe.utils.getdate()
    )

    return balance or 0