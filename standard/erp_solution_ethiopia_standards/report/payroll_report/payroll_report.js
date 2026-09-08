// Copyright (c) 2026, Muhammed Nurhusien
// For license information, please see license.txt

frappe.query_reports["Payroll Report"] = {
    filters: [
        {
            fieldname: "report_type",
            label: __("Report Type"),
            fieldtype: "Select",
            options: [
                "Payroll Sheet",
                "Bank Payment",
                "Deduction",
                "Pay Slip",
                "Pay Summary",
                "Data Summary",
            ],
            default: "Payroll Sheet",
            reqd: 1,
        },
        {
            fieldname: "company_branch",
            label: __("Company Branch"),
            fieldtype: "Link",
            options: "Company Branch",
        },
        {
            fieldname: "budget_year",
            label: __("Budget Year"),
            fieldtype: "Link",
            options: "Budget Year",
        },
        {
            fieldname: "budget_month",
            label: __("Budget Month"),
            fieldtype: "Link",
            options: "Budget Month",
        },
        {
            fieldname: "document_name",
            label: __("Employee Payroll (Document)"),
            fieldtype: "Link",
            options: "Employee Payroll",
        },
        {
            fieldname: "deduction_type",
            label: __("Deduction Type"),
            fieldtype: "Select",
            options: [
                "",
                "Pension (7%)",
                "Income Tax",
                "Credit Association (AWWCE)",
                "ADA",
                "EDIR",
                "AIDS Fund",
                "ANDM",
                "Cost Sharing",
                "Red Cross",
                "Operator Association",
                "Abay Dam",
                "Credit Association (Drilling)",
                "Shemachoche",
                "Defense Contribution",
                "Other 1",
                "Other 2",
                "Other 3",
                "Penalty Deduction",
                "Advance Deduction",
                "Other Variable Deduction 1",
                "Other Variable Deduction 2",
                "Recurring Deduction 1",
                "Recurring Deduction 2",
            ],
            depends_on: "eval:doc.report_type=='Deduction'",
            description: __("Shows only employees with a non-zero amount for this deduction type"),
        },
        {
            fieldname: "employee_id",
            label: __("Employee"),
            fieldtype: "Link",
            options: "Employee",
            depends_on: "eval:doc.report_type=='Pay Slip'",
            description: __("Select one employee to view their individual pay slip"),
        },
    ],

    onload(report) {
        // Re-run automatically when Report Type or Deduction Type changes,
        // so the column set / focused view refreshes without an extra click.
        report.page.wrapper.on(
            "change",
            '[data-fieldname="report_type"], [data-fieldname="deduction_type"], [data-fieldname="employee_id"]',
            () => {
                report.refresh();
            }
        );
    },

    after_datatable_render(datatable) {
        render_payroll_dashboard_cards();
    },
};

// ---------------------------------------------------------------------------
// Ledger-style dashboard card strip
// ---------------------------------------------------------------------------
// The Python side already returns the right numbers via `report_summary`
// (5th element of execute()'s return tuple) for every report type. This
// re-renders those same figures as a set of statement-style cards: dark
// ink surface, tabular monospace amounts, and category-coded accents
// (earnings / deductions / counts / the net-pay hero) instead of a flat
// rainbow gradient grid.

function render_payroll_dashboard_cards() {
    const report = frappe.query_report;
    const summary = (report && report.report_summary) || [];
    if (!summary.length) return;

    inject_ppr_dashboard_styles();

    // ---- category -> accent + icon -----------------------------------
    const CATEGORY = {
        hero: { c1: "#E8B04B", c2: "#B9852C", tint: "rgba(232,176,75,0.14)" },
        earning: { c1: "#33B27C", c2: "#1F7E58", tint: "rgba(51,178,124,0.12)" },
        deduction: { c1: "#E0654B", c2: "#A8412C", tint: "rgba(224,101,75,0.12)" },
        info: { c1: "#4E92D9", c2: "#3468A6", tint: "rgba(78,146,217,0.12)" },
        neutral: { c1: "#8B95A1", c2: "#5F6773", tint: "rgba(139,149,161,0.12)" },
    };

    const category_for = (label) => {
        const l = (label || "").toLowerCase();
        if (/\bnet\b/.test(l)) return "hero";
        if (/tax|pension|deduction|loan|advance|penalty|edir|ada\b|fund|contribution/.test(l))
            return "deduction";
        if (/basic|gross|earning|salary|allowance|overtime|bonus/.test(l)) return "earning";
        if (/employee|document|department|count/.test(l)) return "info";
        return "neutral";
    };

    const icon_for = (label) => {
        const l = (label || "").toLowerCase();
        if (l.includes("employee")) return "\u{1F465}";
        if (l.includes("tax")) return "\u{1F9FE}";
        if (l.includes("pension")) return "\u{1F3E6}";
        if (l.includes("bank") || l.includes("transfer")) return "\u{1F3E6}";
        if (l.includes("net")) return "\u{1F4B0}";
        if (l.includes("loan") || l.includes("advance")) return "\u{1F4C9}";
        if (l.includes("deduction")) return "\u2796";
        if (l.includes("overtime")) return "\u23F1";
        if (l.includes("document")) return "\u{1F4C4}";
        if (l.includes("department")) return "\u{1F3E2}";
        if (l.includes("calculated")) return "\u2705";
        if (l.includes("basic") || l.includes("earning") || l.includes("gross") || l.includes("salary"))
            return "\u{1F4B5}";
        return "\u{1F4CA}";
    };

    // ---- build the eyebrow line (context) -----------------------------
    let report_type = "Payroll Report";
    try {
        report_type = report.get_filter_value("report_type") || report_type;
    } catch (e) {
        /* ignore */
    }
    const today_str = frappe.datetime.str_to_user(frappe.datetime.now_date());

    // ---- build cards ----------------------------------------------------
    const cards_html = summary
        .map((item, idx) => {
            const cat = category_for(item.label);
            const palette = CATEGORY[cat];
            const is_hero = cat === "hero";
            const is_numeric = item.datatype === "Currency" || item.datatype === "Int";
            const raw_num = is_numeric ? Number(item.value) || 0 : null;
            const display_text = is_numeric
                ? "0"
                : frappe.utils.escape_html(String(item.value == null ? "" : item.value));

            return `
                <div class="ppr-card${is_hero ? " ppr-card-hero" : ""}"
                     style="animation-delay:${idx * 55}ms;
                            border-left-color:${palette.c1};
                            --ppr-glow:${palette.c1};">
                    <div class="ppr-card-texture"></div>
                    <div class="ppr-card-top">
                        <span class="ppr-card-label" style="color:${palette.c1}">${frappe.utils.escape_html(
                item.label || ""
            )}</span>
                        <span class="ppr-card-stamp" style="border-color:${palette.c1}88; background:${palette.tint};">
                            <span class="ppr-card-stamp-icon">${icon_for(item.label)}</span>
                        </span>
                    </div>
                    <div class="ppr-card-value"
                         data-numeric="${is_numeric ? "1" : "0"}"
                         data-target="${is_numeric ? raw_num : ""}"
                         data-format="${item.datatype || "Data"}">${display_text}</div>
                </div>
            `;
        })
        .join("");

    const wrapper_html = `
        <div class="ppr-dashboard-wrap">
            <div class="ppr-dashboard-eyebrow">
                <span>${frappe.utils.escape_html(report_type)} \u00B7 ${_("Summary")}</span>
                <span class="ppr-dashboard-date">${_("As of")} ${today_str}</span>
            </div>
            <div class="ppr-dashboard">${cards_html}</div>
        </div>
    `;

    // Remove any previous render of ours before re-inserting.
    $(".ppr-dashboard-wrap").remove();

    // Hide Frappe's default plain-grey summary row (multiple possible
    // selectors across versions -- harmless no-ops if not found).
    $(".report-summary").hide();
    if (report && report.summary_wrapper && report.summary_wrapper.hide) {
        report.summary_wrapper.hide();
    }

    // Insert our version right where the native summary used to sit.
    if (report && report.summary_wrapper && report.summary_wrapper.length) {
        report.summary_wrapper.after(wrapper_html);
    } else if ($(".report-summary").length) {
        $(".report-summary").after(wrapper_html);
    } else {
        // Fallback: place just above the data table.
        $(".dt-scrollable").first().before(wrapper_html);
    }

    animate_ppr_values();
}

function animate_ppr_values() {
    const nodes = document.querySelectorAll(".ppr-card-value[data-numeric='1']");
    nodes.forEach((el) => {
        const target = Number(el.getAttribute("data-target")) || 0;
        const format = el.getAttribute("data-format");
        const duration = 850;
        const start = performance.now();

        const format_value = (num) => {
            if (format === "Currency") {
                return num.toLocaleString(undefined, {
                    minimumFractionDigits: 2,
                    maximumFractionDigits: 2,
                });
            }
            return Math.round(num).toLocaleString();
        };

        function tick(now) {
            const t = Math.min(1, (now - start) / duration);
            const eased = 1 - Math.pow(1 - t, 3); // ease-out-cubic
            el.textContent = format_value(target * eased);
            if (t < 1) requestAnimationFrame(tick);
            else el.textContent = format_value(target);
        }
        requestAnimationFrame(tick);
    });
}

function inject_ppr_dashboard_styles() {
    if (document.getElementById("ppr-dashboard-style")) return;

    const style = document.createElement("style");
    style.id = "ppr-dashboard-style";
    style.innerHTML = `
        .ppr-dashboard-wrap {
            margin: 10px 0 24px 0;
            padding: 18px 20px 20px 20px;
            background: #171D21;
            border-radius: 14px;
            box-shadow: 0 8px 24px rgba(0,0,0,0.22);
        }
        .ppr-dashboard-eyebrow {
            display: flex;
            justify-content: space-between;
            align-items: baseline;
            margin-bottom: 14px;
            padding-bottom: 10px;
            border-bottom: 1px dashed rgba(255,255,255,0.14);
            font-family: ui-monospace, SFMono-Regular, "Roboto Mono", Consolas, monospace;
            font-size: 11px;
            letter-spacing: 0.12em;
            text-transform: uppercase;
            color: rgba(244,241,234,0.55);
        }
        .ppr-dashboard-date {
            letter-spacing: 0.04em;
            text-transform: none;
            opacity: 0.8;
        }
        .ppr-dashboard {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(190px, 1fr));
            gap: 14px;
        }
        .ppr-card {
            position: relative;
            overflow: hidden;
            border-radius: 8px;
            border-left: 4px solid;
            background: linear-gradient(180deg, #1E262B 0%, #171D21 100%);
            padding: 14px 16px 16px 14px;
            box-shadow: 0 2px 6px rgba(0,0,0,0.25);
            transition: transform 0.18s ease, box-shadow 0.18s ease;
            opacity: 0;
            animation: ppr-card-in 0.45s ease forwards;
        }
        .ppr-card:hover {
            transform: translateY(-3px);
            box-shadow: 0 10px 22px rgba(0,0,0,0.35), 0 0 0 1px color-mix(in srgb, var(--ppr-glow) 40%, transparent);
        }
        .ppr-card:hover .ppr-card-stamp {
            transform: rotate(0deg);
        }
        .ppr-card-hero {
            grid-column: span 2;
        }
        .ppr-card-hero .ppr-card-value {
            font-size: 30px;
        }
        .ppr-card-texture {
            position: absolute;
            inset: 0;
            pointer-events: none;
            opacity: 0.05;
            background-image: repeating-linear-gradient(
                0deg,
                #fff 0px,
                #fff 1px,
                transparent 1px,
                transparent 5px
            );
        }
        .ppr-card-top {
            position: relative;
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            margin-bottom: 12px;
        }
        .ppr-card-label {
            font-family: ui-monospace, SFMono-Regular, "Roboto Mono", Consolas, monospace;
            font-size: 10.5px;
            font-weight: 600;
            letter-spacing: 0.08em;
            text-transform: uppercase;
            max-width: 75%;
            line-height: 1.35;
        }
        .ppr-card-stamp {
            flex: 0 0 auto;
            width: 30px;
            height: 30px;
            border-radius: 50%;
            border: 1.5px dashed;
            display: flex;
            align-items: center;
            justify-content: center;
            transform: rotate(-10deg);
            transition: transform 0.25s ease;
        }
        .ppr-card-stamp-icon {
            font-size: 14px;
            line-height: 1;
        }
        .ppr-card-value {
            position: relative;
            font-family: ui-monospace, SFMono-Regular, "Roboto Mono", Consolas, monospace;
            font-variant-numeric: tabular-nums;
            font-size: 22px;
            font-weight: 700;
            letter-spacing: -0.01em;
            color: #F4F1EA;
            word-break: break-word;
        }
        @keyframes ppr-card-in {
            from { opacity: 0; transform: translateY(6px); }
            to   { opacity: 1; transform: translateY(0); }
        }
        @media (max-width: 640px) {
            .ppr-card-hero { grid-column: span 1; }
        }
    `;
    document.head.appendChild(style);
}