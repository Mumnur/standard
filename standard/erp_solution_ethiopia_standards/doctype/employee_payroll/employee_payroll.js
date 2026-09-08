// Copyright (c) 2026, Muhammed Nurhusien
// For license information, please see license.txt

frappe.ui.form.on("Employee Payroll", {
    refresh(frm) {
        render_payroll_buttons(frm);
    }
});

function render_payroll_buttons(frm) {

    frm.clear_custom_buttons();

    const sheet = frm.doc.employee_payroll_sheet || [];
    const has_employees = sheet.length > 0;

    const has_fixed = !!frm.doc.fixed_components_fetched;
    const has_variable = !!frm.doc.variable_components_fetched;
    const has_recurring = !!frm.doc.recurring_deductions_fetched;
    const has_attendance = !!frm.doc.attendance_fetched;
    const has_calculated = !!frm.doc.payroll_calculated;

    if (!has_employees) {
        frm.add_custom_button(__("Fetch Employee Information"),
            () => fetch_employee_information(frm), __("Payroll Actions"));
        return;
    }

    if (!has_fixed) {
        frm.add_custom_button(__("Fetch Fixed Salary Components"),
            () => fetch_fixed_salary_components(frm), __("Payroll Actions"));
        return;
    }

    if (!has_variable) {
        frm.add_custom_button(__("Fetch Variable Salary Components"),
            () => fetch_variable_salary_components(frm), __("Payroll Actions"));
        return;
    }

    if (!has_recurring) {
        frm.add_custom_button(__("Fetch Recurring Deduction Components"),
            () => fetch_recurring_deduction_components(frm), __("Payroll Actions"));
        return;
    }

    if (!has_attendance) {
        frm.add_custom_button(__("Fetch Attendance and Overtime"),
            () => fetch_attendance_and_overtime(frm), __("Payroll Actions"));
        return;
    }

    if (!has_calculated) {
        frm.add_custom_button(__("Calculate Payroll"),
            () => calculate_payroll(frm), __("Payroll Actions"));
        return;
    }

    frm.add_custom_button(__("Start Over"), () => {
        frappe.confirm(
            __("This will clear all fetched data and reset the workflow. Continue?"),
            () => {
                frm.clear_table("employee_payroll_sheet");
                frm.refresh_field("employee_payroll_sheet");
                frm.set_value("fixed_components_fetched", 0);
                frm.set_value("variable_components_fetched", 0);
                frm.set_value("recurring_deductions_fetched", 0);
                frm.set_value("attendance_fetched", 0);
                frm.set_value("payroll_calculated", 0);
                render_payroll_buttons(frm);
            }
        );
    }, __("Payroll Actions"));
}

const INCOME_TAX_SLABS = [
    { min: 0,     max: 2000,     rate: 0.00, deduction: 0.00 },
    { min: 2001,  max: 4000,     rate: 0.15, deduction: 300.00 },
    { min: 4001,  max: 7000,     rate: 0.20, deduction: 500.00 },
    { min: 7001,  max: 10000,    rate: 0.25, deduction: 850.00 },
    { min: 10001, max: 14000,    rate: 0.30, deduction: 1350.00 },
    { min: 14001, max: Infinity, rate: 0.35, deduction: 2050.00 }
];

function calculate_income_tax(taxable_amount) {
    taxable_amount = flt(taxable_amount);
    for (const slab of INCOME_TAX_SLABS) {
        if (taxable_amount >= slab.min && taxable_amount <= slab.max) {
            const tax = taxable_amount * slab.rate - slab.deduction;
            return tax > 0 ? tax : 0;
        }
    }
    return 0;
}

function flt(v) {
    const n = parseFloat(v);
    return isNaN(n) ? 0 : n;
}

// ===================================
// Step 6: Calculate Payroll
// ===================================
function calculate_payroll(frm) {

    if (!frm.doc.employee_payroll_sheet.length) {
        frappe.msgprint(__("Please fetch employee information first."));
        return;
    }

    frm.doc.employee_payroll_sheet.forEach(function (row) {

        row.working_days_salary = flt(row.basic_salary) * flt(row.working_days) / 30;

        row.total_taxable_allowance =
            flt(row.taxable_transport_allowance) +
            flt(row.working_days_salary) + 
            flt(row.overtime) +
            flt(row.taxable_professional_allowance) +
            flt(row.other_taxable_allowance) +
            flt(row.taxable_positional_allowance) +
            flt(row.other_taxable_allowance_two) +
            flt(row.acting_allowance) +
            flt(row.incentive_allowance);

        row.total_non_taxable_amount =
            flt(row.nontaxable_transport_allowance) +
            flt(row.other_nontaxable_allowance) +
            flt(row.other_nontaxable_allowance_two);

        row.total_earning = row.total_taxable_allowance + row.total_non_taxable_amount;

        row.pension_7 = flt(row.basic_salary) * 0.07;
        row.pension_11 = flt(row.basic_salary) * 0.11;

        row.income_tax = calculate_income_tax(row.total_taxable_allowance);

        const other_deductions =
            flt(row.credit_association_awwce) +
            flt(row.ada) +
            flt(row.edir) +
            flt(row.aids_fund) +
            flt(row.andm) +
            flt(row.cost_sharing) +
            flt(row.red_cross) +
            flt(row.operator_association) +
            flt(row.abay_dam) +
            flt(row.credit_association_drilling) +
            flt(row.shemachoche) +
            flt(row.defense_contribution) +
            flt(row.other_one) +
            flt(row.other_two) +
            flt(row.other_three) +
            flt(row.penalty_deduction) +
            flt(row.advance_deduction) +
            flt(row.other_variable_deduction_one) +
            flt(row.other_variable_deduction_two) +
            flt(row.recurring_deduction_one) +
            flt(row.recurring_deduction_two);

        row.total_deduction = row.pension_7 + row.income_tax + other_deductions;

        row.net_payment = row.total_earning - row.total_deduction;
    });

    frm.refresh_field("employee_payroll_sheet");
    frm.set_value("payroll_calculated", 1);

    frappe.show_alert({
        message: __("Payroll calculated successfully."),
        indicator: "green"
    });

    render_payroll_buttons(frm);
}

// ============================
// Step 1: Fetch Employee Information
// ============================
function fetch_employee_information(frm) {

    if (!frm.doc.company_branch) {
        frappe.msgprint(__("Please select Company Branch."));
        return;
    }

    frappe.call({
        method: "standard.erp_solution_ethiopia_standards.doctype.employee_payroll.employee_payroll.fetch_employee_information",
        args: {
            company_branch: frm.doc.company_branch
        },
        freeze: true,
        freeze_message: __("Fetching Employees..."),
        callback: function (r) {

            if (!r.message) return;

            frm.clear_table("employee_payroll_sheet");

            r.message.forEach(function (emp) {
                let row = frm.add_child("employee_payroll_sheet");
                row.employee_id = emp.name;
                row.employee_name = emp.employee_name;
                row.company_branch = emp.custom_branch;
                row.department = emp.department;
                row.cost_center = emp.payroll_cost_center;
                row.project = emp.custom_project;
                row.employment_type = emp.employment_type;
                row.designation = emp.designation;
                row.date_of_joining_ec = emp.custom_date_of_joining_date_ec;
                row.date_of_joining = emp.date_of_joining;
                row.tin_number = emp.custom_tin_number;
                row.pension_no = emp.custom_pension_number;
                row.pension = emp.custom_pension;
            });

            frm.refresh_field("employee_payroll_sheet");

            frappe.show_alert({
                message: __("Employee information fetched successfully ({0} employees).", [r.message.length]),
                indicator: "green"
            });

            render_payroll_buttons(frm);
        }
    });
}

// ===================================
// Step 2: Fetch Fixed Salary Components
// ===================================
function fetch_fixed_salary_components(frm) {

    if (!frm.doc.employee_payroll_sheet.length) {
        frappe.msgprint(__("Please fetch employee information first."));
        return;
    }

    frappe.call({
        method: "standard.erp_solution_ethiopia_standards.doctype.employee_payroll.employee_payroll.fetch_fixed_salary_components",
        args: {
            employees: frm.doc.employee_payroll_sheet.map(d => d.employee_id)
        },
        freeze: true,
        freeze_message: __("Fetching Fixed Salary Components..."),
        callback: function (r) {

            if (!r.message) return;

            const salary_data = r.message;

            frm.doc.employee_payroll_sheet.forEach(function (row) {

                const emp = salary_data[row.employee_id];
                if (!emp) return;

                row.bank_ac_no = emp.bank_ac_no;
                row.basic_salary = emp.basic_salary;

                row.taxable_transport_allowance = emp.taxable_transport_allowance;
                row.taxable_professional_allowance = emp.taxable_professional_allowance;
                row.other_taxable_allowance = emp.other_taxable_allowance;
                row.taxable_positional_allowance = emp.taxable_positional_allowance;
                row.nontaxable_transport_allowance = emp.nontaxable_transport_allowance;
                row.other_nontaxable_allowance = emp.other_nontaxable_allowance;

                row.credit_association_awwce = emp.credit_association;
                row.ada = emp.ada;
                row.edir = emp.edir;
                row.aids_fund = emp.aids_fund;
                row.andm = emp.andm;
                row.cost_sharing = emp.cost_sharing;
                row.red_cross = emp.red_cross;
                row.operator_association = emp.operator_association;
                row.abay_dam = emp.abay_dam;
                row.credit_association_drilling = emp.credit_association_rig;
                row.shemachoche = emp.shemachoche;
                row.defense_contribution = emp.defense_contribution;
                row.other_one = emp.other_one;
                row.other_two = emp.other_two;
                row.other_three = emp.other_three;
            });

            frm.refresh_field("employee_payroll_sheet");
            frm.set_value("fixed_components_fetched", 1);

            frappe.show_alert({
                message: __("Fixed Salary Components fetched successfully."),
                indicator: "green"
            });

            render_payroll_buttons(frm);
        }
    });
}

// ===================================
// Step 3: Fetch Variable Salary Components
// ===================================
function fetch_variable_salary_components(frm) {

    if (!frm.doc.budget_year || !frm.doc.budget_month) {
        frappe.msgprint(__("Please select Budget Year and Budget Month."));
        return;
    }

    if (!frm.doc.employee_payroll_sheet.length) {
        frappe.msgprint(__("Please fetch employee information first."));
        return;
    }

    frappe.call({
        method: "standard.erp_solution_ethiopia_standards.doctype.employee_payroll.employee_payroll.fetch_variable_salary_components",
        args: {
            budget_year: frm.doc.budget_year,
            budget_month: frm.doc.budget_month,
            employees: frm.doc.employee_payroll_sheet.map(d => d.employee_id)
        },
        freeze: true,
        freeze_message: __("Fetching Variable Salary Components..."),
        callback: function (r) {

            if (!r.message) return;

            let variable_data = r.message;

            frm.doc.employee_payroll_sheet.forEach(function (row) {

                let emp = variable_data[row.employee_id];
                if (!emp) return; // no variable record for this employee this month

                row.acting_allowance = emp.acting_allowance;
                row.incentive_allowance = emp.incentive_allowance;

                row.other_taxable_allowance_two = emp.other_taxable_allowance;
                row.other_nontaxable_allowance_two = emp.other_nontaxable_allowance;

                row.penalty_deduction = emp.penalty_deduction;
                row.advance_deduction = emp.advance_deduction;

                row.other_variable_deduction_one = emp.other_variable_deduction_one;
                row.other_variable_deduction_two = emp.other_variable_deduction_two;
            });

            frm.refresh_field("employee_payroll_sheet");
            frm.set_value("variable_components_fetched", 1);

            frappe.show_alert({
                message: __("Variable Salary Components fetched successfully."),
                indicator: "green"
            });

            render_payroll_buttons(frm);
        }
    });
}

// ===================================
// Step 4: Fetch Recurring Deduction Components
// ===================================
function fetch_recurring_deduction_components(frm) {

    if (!frm.doc.budget_year || !frm.doc.budget_month) {
        frappe.msgprint(__("Please select Budget Year and Budget Month."));
        return;
    }

    if (!frm.doc.employee_payroll_sheet.length) {
        frappe.msgprint(__("Please fetch employee information first."));
        return;
    }

    frappe.call({
        method: "standard.erp_solution_ethiopia_standards.doctype.employee_payroll.employee_payroll.fetch_recurring_deduction_components",
        args: {
            employees: frm.doc.employee_payroll_sheet.map(d => d.employee_id),
            budget_year: frm.doc.budget_year,
            budget_month: frm.doc.budget_month
        },
        freeze: true,
        freeze_message: __("Fetching Recurring Deductions..."),
        callback: function (r) {

            if (!r.message) return;

            const deduction_data = r.message;

            frm.doc.employee_payroll_sheet.forEach(function (row) {

                const emp = deduction_data[row.employee_id];

                row.recurring_deduction_one = (emp && emp.recurring_deduction_one) || 0;
                row.recurring_deduction_two = (emp && emp.recurring_deduction_two) || 0;
            });

            frm.refresh_field("employee_payroll_sheet");
            frm.set_value("recurring_deductions_fetched", 1);

            frappe.show_alert({
                message: __("Recurring Deduction Components fetched successfully."),
                indicator: "green"
            });

            render_payroll_buttons(frm);
        }
    });
}

// ===================================
// Step 5: Fetch Attendance and Overtime
// ===================================
function fetch_attendance_and_overtime(frm) {

    if (!frm.doc.budget_year || !frm.doc.budget_month) {
        frappe.msgprint(__("Please select Budget Year and Budget Month."));
        return;
    }

    if (!frm.doc.employee_payroll_sheet.length) {
        frappe.msgprint(__("Please fetch employee information first."));
        return;
    }

    frappe.call({
        method: "standard.erp_solution_ethiopia_standards.doctype.employee_payroll.employee_payroll.fetch_attendance_and_overtime",
        args: {
            budget_year: frm.doc.budget_year,
            budget_month: frm.doc.budget_month,
            employees: frm.doc.employee_payroll_sheet.map(d => d.employee_id)
        },
        freeze: true,
        freeze_message: __("Fetching Attendance and Overtime..."),
        callback: function (r) {

            if (!r.message) return;

            let data = r.message;

            frm.doc.employee_payroll_sheet.forEach(function (row) {

                let emp = data[row.employee_id];

                row.working_days = (emp && emp.working_days) || 0;
                row.overtime = (emp && emp.overtime) || 0;
            });

            frm.refresh_field("employee_payroll_sheet");
            frm.set_value("attendance_fetched", 1);

            frappe.show_alert({
                message: __("Attendance and Overtime fetched successfully."),
                indicator: "green"
            });

            render_payroll_buttons(frm);
        }
    });
}