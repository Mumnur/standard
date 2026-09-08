import frappe

from frappe import _
from frappe.utils import getdate, add_days
from erpnext.accounts.utils import get_fiscal_year


# ============================================================
# ACCOUNT SETTINGS
# ============================================================

# ------------------------------------------------------------
# Companies Receivable
# ------------------------------------------------------------

COMPANIES_RECEIVABLE_ACCOUNT = (
    "11202-0004 - Prepayment Receivable - WWC"
)


# ------------------------------------------------------------
# Staff Receivable
# ------------------------------------------------------------

STAFF_RECEIVABLE_ACCOUNT = (
    "11202-0003 - Staff Receivable - WWC"
)


# ------------------------------------------------------------
# Purchase Fund
# ------------------------------------------------------------

PURCHASE_FUND_PARENT_ACCOUNT = (
    "11104 - Purchase Fund - WWC"
)


# ------------------------------------------------------------
# Cashier
# ------------------------------------------------------------

CASHIER_PARENT_ACCOUNTS = [
    "11101 - Cash On Hand - WWC",
    "11102 - Petty Cash - WWC",
    "11103 - Payroll Fund - WWC",
]


# ============================================================
# EXECUTE
# ============================================================

def execute(filters=None):

    filters = frappe._dict(filters or {})

    validate_filters(filters)

    columns = get_columns()

    data = get_data(filters)

    chart = get_chart(data)

    return columns, data, None, chart


# ============================================================
# VALIDATION
# ============================================================

def validate_filters(filters):

    if not filters.get("reporting_date"):

        frappe.throw(
            _("Reporting Date is required")
        )


# ============================================================
# COLUMNS
# ============================================================

def get_columns():

    return [

        {
            "fieldname": "company_branch",
            "label": _("Company Branch"),
            "fieldtype": "Link",
            "options": "Company Branch",
            "width": 200,
        },

        {
            "fieldname": "companies_receivable",
            "label": _("Companies Receivable"),
            "fieldtype": "Currency",
            "width": 190,
        },

        {
            "fieldname": "staff_receivable",
            "label": _("Staff Receivable"),
            "fieldtype": "Currency",
            "width": 180,
        },

        {
            "fieldname": "purchase_fund_receivable",
            "label": _("Purchase Fund Receivable"),
            "fieldtype": "Currency",
            "width": 210,
        },

        {
            "fieldname": "cashier_receivable",
            "label": _("Cashier Receivable"),
            "fieldtype": "Currency",
            "width": 180,
        },

        {
            "fieldname": "total_receivable",
            "label": _("Total Receivable"),
            "fieldtype": "Currency",
            "width": 180,
        },

    ]


# ============================================================
# GET LEAF ACCOUNTS UNDER PARENT
# ============================================================

def get_leaf_accounts(parent_account_name):

    parent = frappe.db.get_value(
        "Account",
        parent_account_name,
        [
            "name",
            "lft",
            "rgt",
            "is_group",
        ],
        as_dict=True,
    )

    if not parent:

        frappe.throw(
            _(
                "Account {0} was not found."
            ).format(
                frappe.bold(parent_account_name)
            )
        )

    # --------------------------------------------------------
    # Parent is a group account
    # --------------------------------------------------------

    if parent.is_group:

        accounts = frappe.get_all(
            "Account",
            filters={
                "lft": [">=", parent.lft],
                "rgt": ["<=", parent.rgt],
                "is_group": 0,
            },
            pluck="name",
            order_by="lft",
        )

    # --------------------------------------------------------
    # Account itself is a ledger account
    # --------------------------------------------------------

    else:

        accounts = [
            parent.name
        ]

    return accounts


# ============================================================
# GET COMPANIES RECEIVABLE ACCOUNTS
# ============================================================

def get_companies_receivable_accounts():

    account = COMPANIES_RECEIVABLE_ACCOUNT

    # --------------------------------------------------------
    # Validate account exists
    # --------------------------------------------------------

    account_exists = frappe.db.exists(
        "Account",
        account
    )

    if not account_exists:

        frappe.throw(
            _(
                "Companies Receivable account {0} was not found."
            ).format(
                frappe.bold(account)
            )
        )

    # --------------------------------------------------------
    # Return ONLY this account
    # --------------------------------------------------------

    return [
        account
    ]


# ============================================================
# GET PURCHASE FUND ACCOUNTS
# ============================================================

def get_purchase_fund_accounts():

    accounts = get_leaf_accounts(
        PURCHASE_FUND_PARENT_ACCOUNT
    )

    if not accounts:

        frappe.throw(
            _(
                "No Purchase Fund accounts were found."
            )
        )

    return accounts


# ============================================================
# GET CASHIER ACCOUNTS
# ============================================================

def get_cashier_accounts():

    accounts = []

    for parent_account in CASHIER_PARENT_ACCOUNTS:

        accounts.extend(
            get_leaf_accounts(
                parent_account
            )
        )

    # --------------------------------------------------------
    # Remove duplicates
    # --------------------------------------------------------

    accounts = list(
        dict.fromkeys(accounts)
    )

    if not accounts:

        frappe.throw(
            _(
                "No Cashier accounts were found."
            )
        )

    return accounts


# ============================================================
# GET BALANCE BY ACCOUNT SET
# ============================================================

def get_receivable_balance_by_branch(
    accounts,
    reporting_date,
    fiscal_year_start
):

    previous_year_end = add_days(
        fiscal_year_start,
        -1
    )

    # ========================================================
    # GET GL ENTRIES
    # ========================================================

    gl_entries = frappe.db.sql(
        """
        SELECT

            gle.name,

            gle.account,

            gle.company_branch,

            gle.party_type,

            gle.party,

            gle.posting_date,

            gle.debit,

            gle.credit

        FROM `tabGL Entry` gle

        WHERE

            gle.account IN %(accounts)s

            AND gle.posting_date <= %(reporting_date)s

            AND gle.is_cancelled = 0

            AND IFNULL(
                gle.company_branch,
                ''
            ) != ''

        ORDER BY

            gle.company_branch,

            gle.party,

            gle.posting_date,

            gle.name

        """,
        {
            "accounts": accounts,
            "reporting_date": reporting_date,
        },
        as_dict=True,
    )

    # ========================================================
    # PARTY + COMPANY BRANCH
    # ========================================================

    party_branch_data = {}

    for row in gl_entries:

        company_branch = (
            row.company_branch
            or _("Not Set")
        )

        party = (
            row.party
            or _("Unknown Party")
        )

        key = (
            company_branch,
            party
        )

        if key not in party_branch_data:

            party_branch_data[key] = {

                "last_year_balance": 0,

                "current_year_debit": 0,

                "current_year_credit": 0,

            }

        debit = row.debit or 0

        credit = row.credit or 0

        posting_date = getdate(
            row.posting_date
        )

        # ====================================================
        # LAST YEAR
        # ====================================================

        if posting_date <= previous_year_end:

            party_branch_data[key][
                "last_year_balance"
            ] += (
                debit - credit
            )

        # ====================================================
        # CURRENT YEAR
        # ====================================================

        elif (
            posting_date >= fiscal_year_start
            and posting_date <= reporting_date
        ):

            party_branch_data[key][
                "current_year_debit"
            ] += debit

            party_branch_data[key][
                "current_year_credit"
            ] += credit

    # ========================================================
    # AGGREGATE BY COMPANY BRANCH
    # ========================================================

    branch_balances = {}

    for (
        company_branch,
        party
    ), values in party_branch_data.items():

        if company_branch not in branch_balances:

            branch_balances[
                company_branch
            ] = 0

        # ----------------------------------------------------
        # Opening balance
        # ----------------------------------------------------

        opening_balance = (
            values["last_year_balance"]
        )

        # ----------------------------------------------------
        # Current year debit
        # ----------------------------------------------------

        current_year_debit = (
            values["current_year_debit"]
        )

        # ----------------------------------------------------
        # Current year credit
        # ----------------------------------------------------

        current_year_credit = (
            values["current_year_credit"]
        )

        # ====================================================
        # RECONCILED
        # ====================================================

        reconciled = min(
            current_year_credit,
            max(
                opening_balance,
                0
            )
        )

        # ====================================================
        # UNRECONCILED
        # ====================================================

        unreconciled = max(
            opening_balance
            - reconciled,
            0
        )

        # ====================================================
        # EXCESS CREDIT
        # ====================================================

        excess_credit = max(
            current_year_credit
            - opening_balance,
            0
        )

        # ====================================================
        # CURRENT YEAR BALANCE
        # ====================================================

        current_year_balance = (
            current_year_debit
            - excess_credit
        )

        # ====================================================
        # TOTAL REPORTING DATE BALANCE
        # ====================================================

        total_reporting_date_balance = (
            unreconciled
            + current_year_balance
        )

        branch_balances[
            company_branch
        ] += total_reporting_date_balance

    return branch_balances


# ============================================================
# GET DATA
# ============================================================

def get_data(filters):

    reporting_date = getdate(
        filters.get("reporting_date")
    )

    # ========================================================
    # FISCAL YEAR
    # ========================================================

    fiscal_year_info = get_fiscal_year(
        reporting_date,
        company=None,
        as_dict=True
    )

    fiscal_year_start = getdate(
        fiscal_year_info.year_start_date
    )

    # ========================================================
    # GET ACCOUNT LISTS
    # ========================================================

    # ONLY:
    # 11202-0004 - Prepayment Receivable - WWC

    companies_accounts = (
        get_companies_receivable_accounts()
    )

    # ONLY:
    # 11202-0003 - Staff Receivable - WWC

    staff_accounts = [
        STAFF_RECEIVABLE_ACCOUNT
    ]

    # Purchase Fund

    purchase_fund_accounts = (
        get_purchase_fund_accounts()
    )

    # Cashier

    cashier_accounts = (
        get_cashier_accounts()
    )

    # ========================================================
    # CALCULATE EACH TYPE
    # ========================================================

    companies_balances = (
        get_receivable_balance_by_branch(
            companies_accounts,
            reporting_date,
            fiscal_year_start
        )
    )

    staff_balances = (
        get_receivable_balance_by_branch(
            staff_accounts,
            reporting_date,
            fiscal_year_start
        )
    )

    purchase_fund_balances = (
        get_receivable_balance_by_branch(
            purchase_fund_accounts,
            reporting_date,
            fiscal_year_start
        )
    )

    cashier_balances = (
        get_receivable_balance_by_branch(
            cashier_accounts,
            reporting_date,
            fiscal_year_start
        )
    )

    # ========================================================
    # GET ALL COMPANY BRANCHES
    # ========================================================

    company_branches = set()

    company_branches.update(
        companies_balances.keys()
    )

    company_branches.update(
        staff_balances.keys()
    )

    company_branches.update(
        purchase_fund_balances.keys()
    )

    company_branches.update(
        cashier_balances.keys()
    )

    # ========================================================
    # BUILD FINAL REPORT
    # ========================================================

    data = []

    for company_branch in sorted(
        company_branches
    ):

        # ----------------------------------------------------
        # Companies Receivable
        # ONLY 11202-0004
        # ----------------------------------------------------

        companies_receivable = (
            companies_balances.get(
                company_branch,
                0
            )
        )

        # ----------------------------------------------------
        # Staff Receivable
        # ----------------------------------------------------

        staff_receivable = (
            staff_balances.get(
                company_branch,
                0
            )
        )

        # ----------------------------------------------------
        # Purchase Fund Receivable
        # ----------------------------------------------------

        purchase_fund_receivable = (
            purchase_fund_balances.get(
                company_branch,
                0
            )
        )

        # ----------------------------------------------------
        # Cashier Receivable
        # ----------------------------------------------------

        cashier_receivable = (
            cashier_balances.get(
                company_branch,
                0
            )
        )

        # ====================================================
        # TOTAL RECEIVABLE
        # ====================================================

        total_receivable = (
            companies_receivable
            + staff_receivable
            + purchase_fund_receivable
            + cashier_receivable
        )

        data.append({

            "company_branch":
                company_branch,

            "companies_receivable":
                companies_receivable,

            "staff_receivable":
                staff_receivable,

            "purchase_fund_receivable":
                purchase_fund_receivable,

            "cashier_receivable":
                cashier_receivable,

            "total_receivable":
                total_receivable,

        })

    return data


# ============================================================
# CHART
# ============================================================

def get_chart(data):

    if not data:

        return None

    labels = []

    companies_values = []

    staff_values = []

    purchase_fund_values = []

    cashier_values = []

    total_values = []

    for row in data:

        labels.append(
            row.get(
                "company_branch"
            )
        )

        companies_values.append(
            row.get(
                "companies_receivable"
            ) or 0
        )

        staff_values.append(
            row.get(
                "staff_receivable"
            ) or 0
        )

        purchase_fund_values.append(
            row.get(
                "purchase_fund_receivable"
            ) or 0
        )

        cashier_values.append(
            row.get(
                "cashier_receivable"
            ) or 0
        )

        total_values.append(
            row.get(
                "total_receivable"
            ) or 0
        )

    return {

        "data": {

            "labels": labels,

            "datasets": [

                {
                    "name":
                        _("Companies Receivable"),

                    "values":
                        companies_values,
                },

                {
                    "name":
                        _("Staff Receivable"),

                    "values":
                        staff_values,
                },

                {
                    "name":
                        _("Purchase Fund Receivable"),

                    "values":
                        purchase_fund_values,
                },

                {
                    "name":
                        _("Cashier Receivable"),

                    "values":
                        cashier_values,
                },

                {
                    "name":
                        _("Total Receivable"),

                    "values":
                        total_values,
                },

            ],

        },

        "type": "bar",

        "height": 350,

    }