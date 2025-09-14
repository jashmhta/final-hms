"""
Management command to initialize Chart of Accounts for hospitals.
"""

from django.core.management.base import BaseCommand

from accounting.models import AccountSubType, AccountType, ChartOfAccounts, Currency
from hospitals.models import Hospital


class Command(BaseCommand):
    help = "Initialize Chart of Accounts for hospitals"

    def add_arguments(self, parser):
        parser.add_argument(
            "--hospital-id",
            type=int,
            help="Hospital ID to initialize accounts for (optional - if not provided, initializes for all)",  # noqa: E501      # noqa: E501
        )

    def handle(self, *args, **options):
        hospital_id = options.get("hospital_id")

        if hospital_id:
            hospitals = Hospital.objects.filter(id=hospital_id)
        else:
            hospitals = Hospital.objects.all()

        for hospital in hospitals:
            self.stdout.write(
                f"Initializing Chart of Accounts for {hospital.name}..."
            )  # noqa: E501
            self.initialize_accounts_for_hospital(hospital)
            self.stdout.write(
                self.style.SUCCESS(
                    f"Successfully initialized accounts for {hospital.name}"
                )
            )

    def initialize_accounts_for_hospital(self, hospital):
        """Initialize standard chart of accounts for a hospital"""

        # Ensure base currency exists
        base_currency, created = Currency.objects.get_or_create(
            hospital=hospital,
            code="INR",
            defaults={
                "name": "Indian Rupee",
                "symbol": "₹",
                "is_base_currency": True,
                "exchange_rate": 1.0000,
            },
        )

        # Standard Chart of Accounts for Healthcare
        accounts_data = [
            # ASSETS
            (
                "1000",
                "ASSETS",
                "Assets",
                AccountType.ASSETS,
                AccountSubType.CURRENT_ASSETS,
                None,
                True,
            ),
            # Current Assets
            (
                "1100",
                "Cash in Hand",
                "Cash in Hand",
                AccountType.ASSETS,
                AccountSubType.CURRENT_ASSETS,
                "1000",
                True,
            ),
            (
                "1150",
                "Cash at Bank",
                "Cash at Bank",
                AccountType.ASSETS,
                AccountSubType.CURRENT_ASSETS,
                "1000",
                True,
            ),
            (
                "1200",
                "Accounts Receivable",
                "Accounts Receivable",
                AccountType.ASSETS,
                AccountSubType.CURRENT_ASSETS,
                "1000",
                True,
            ),
            (
                "1250",
                "Insurance Receivables",
                "Insurance Receivables",
                AccountType.ASSETS,
                AccountSubType.CURRENT_ASSETS,
                "1000",
                True,
            ),
            (
                "1300",
                "Inventory - Medical Supplies",
                "Medical Supplies Inventory",
                AccountType.ASSETS,
                AccountSubType.CURRENT_ASSETS,
                "1000",
                True,
            ),
            (
                "1310",
                "Inventory - Pharmaceuticals",
                "Pharmaceutical Inventory",
                AccountType.ASSETS,
                AccountSubType.CURRENT_ASSETS,
                "1000",
                True,
            ),
            (
                "1400",
                "TDS Receivable",
                "TDS Receivable",
                AccountType.ASSETS,
                AccountSubType.CURRENT_ASSETS,
                "1000",
                True,
            ),
            (
                "1450",
                "Prepaid Expenses",
                "Prepaid Expenses",
                AccountType.ASSETS,
                AccountSubType.CURRENT_ASSETS,
                "1000",
                True,
            ),
            # Fixed Assets
            (
                "1500",
                "Fixed Assets",
                "Fixed Assets",
                AccountType.ASSETS,
                AccountSubType.FIXED_ASSETS,
                "1000",
                True,
            ),
            (
                "1510",
                "Medical Equipment",
                "Medical Equipment",
                AccountType.ASSETS,
                AccountSubType.FIXED_ASSETS,
                "1500",
                True,
            ),
            (
                "1520",
                "IT Equipment",
                "IT Equipment",
                AccountType.ASSETS,
                AccountSubType.FIXED_ASSETS,
                "1500",
                True,
            ),
            (
                "1530",
                "Furniture & Fixtures",
                "Furniture & Fixtures",
                AccountType.ASSETS,
                AccountSubType.FIXED_ASSETS,
                "1500",
                True,
            ),
            (
                "1540",
                "Vehicles",
                "Vehicles",
                AccountType.ASSETS,
                AccountSubType.FIXED_ASSETS,
                "1500",
                True,
            ),
            (
                "1550",
                "Building",
                "Building",
                AccountType.ASSETS,
                AccountSubType.FIXED_ASSETS,
                "1500",
                True,
            ),
            (
                "1560",
                "Land",
                "Land",
                AccountType.ASSETS,
                AccountSubType.FIXED_ASSETS,
                "1500",
                True,
            ),
            (
                "1590",
                "Accumulated Depreciation",
                "Accumulated Depreciation",
                AccountType.ASSETS,
                AccountSubType.FIXED_ASSETS,
                "1500",
                True,
            ),
            # LIABILITIES
            (
                "2000",
                "LIABILITIES",
                "Liabilities",
                AccountType.LIABILITIES,
                AccountSubType.CURRENT_LIABILITIES,
                None,
                True,
            ),
            # Current Liabilities
            (
                "2100",
                "Accounts Payable",
                "Accounts Payable",
                AccountType.LIABILITIES,
                AccountSubType.CURRENT_LIABILITIES,
                "2000",
                True,
            ),
            (
                "2200",
                "Accrued Expenses",
                "Accrued Expenses",
                AccountType.LIABILITIES,
                AccountSubType.CURRENT_LIABILITIES,
                "2000",
                True,
            ),
            (
                "2300",
                "TDS Payable",
                "TDS Payable",
                AccountType.LIABILITIES,
                AccountSubType.CURRENT_LIABILITIES,
                "2000",
                True,
            ),
            (
                "2350",
                "GST Payable",
                "GST Payable",
                AccountType.LIABILITIES,
                AccountSubType.CURRENT_LIABILITIES,
                "2000",
                True,
            ),
            (
                "2400",
                "Salary Payable",
                "Salary Payable",
                AccountType.LIABILITIES,
                AccountSubType.CURRENT_LIABILITIES,
                "2000",
                True,
            ),
            (
                "2410",
                "PF Payable",
                "Provident Fund Payable",
                AccountType.LIABILITIES,
                AccountSubType.CURRENT_LIABILITIES,
                "2000",
                True,
            ),
            (
                "2420",
                "ESI Payable",
                "ESI Payable",
                AccountType.LIABILITIES,
                AccountSubType.CURRENT_LIABILITIES,
                "2000",
                True,
            ),
            (
                "2500",
                "Short Term Loans",
                "Short Term Loans",
                AccountType.LIABILITIES,
                AccountSubType.CURRENT_LIABILITIES,
                "2000",
                True,
            ),
            # Long Term Liabilities
            (
                "2600",
                "Long Term Loans",
                "Long Term Loans",
                AccountType.LIABILITIES,
                AccountSubType.LONG_TERM_LIABILITIES,
                "2000",
                True,
            ),
            # EQUITY
            (
                "3000",
                "EQUITY",
                "Equity",
                AccountType.EQUITY,
                AccountSubType.CURRENT_ASSETS,
                None,
                True,
            ),
            (
                "3100",
                "Share Capital",
                "Share Capital",
                AccountType.EQUITY,
                AccountSubType.CURRENT_ASSETS,
                "3000",
                True,
            ),
            (
                "3200",
                "Retained Earnings",
                "Retained Earnings",
                AccountType.EQUITY,
                AccountSubType.CURRENT_ASSETS,
                "3000",
                True,
            ),
            (
                "3300",
                "Current Year Earnings",
                "Current Year Earnings",
                AccountType.EQUITY,
                AccountSubType.CURRENT_ASSETS,
                "3000",
                True,
            ),
            # INCOME
            (
                "4000",
                "INCOME",
                "Income",
                AccountType.INCOME,
                AccountSubType.OPERATING_INCOME,
                None,
                True,
            ),
            # Operating Income
            (
                "4100",
                "Patient Services Revenue",
                "Patient Services Revenue",
                AccountType.INCOME,
                AccountSubType.OPERATING_INCOME,
                "4000",
                True,
            ),
            (
                "4110",
                "Consultation Fees",
                "Consultation Fees",
                AccountType.INCOME,
                AccountSubType.OPERATING_INCOME,
                "4100",
                True,
            ),
            (
                "4120",
                "Surgery Fees",
                "Surgery Fees",
                AccountType.INCOME,
                AccountSubType.OPERATING_INCOME,
                "4100",
                True,
            ),
            (
                "4130",
                "Diagnostic Fees",
                "Diagnostic Fees",
                AccountType.INCOME,
                AccountSubType.OPERATING_INCOME,
                "4100",
                True,
            ),
            (
                "4140",
                "Laboratory Fees",
                "Laboratory Fees",
                AccountType.INCOME,
                AccountSubType.OPERATING_INCOME,
                "4100",
                True,
            ),
            (
                "4150",
                "Pharmacy Sales",
                "Pharmacy Sales",
                AccountType.INCOME,
                AccountSubType.OPERATING_INCOME,
                "4100",
                True,
            ),
            (
                "4160",
                "Room Charges",
                "Room Charges",
                AccountType.INCOME,
                AccountSubType.OPERATING_INCOME,
                "4100",
                True,
            ),
            (
                "4170",
                "Package Revenue",
                "Package Revenue",
                AccountType.INCOME,
                AccountSubType.OPERATING_INCOME,
                "4100",
                True,
            ),
            (
                "4200",
                "Insurance Revenue",
                "Insurance Revenue",
                AccountType.INCOME,
                AccountSubType.OPERATING_INCOME,
                "4000",
                True,
            ),
            (
                "4300",
                "Corporate Revenue",
                "Corporate Revenue",
                AccountType.INCOME,
                AccountSubType.OPERATING_INCOME,
                "4000",
                True,
            ),
            # Non-Operating Income
            (
                "4900",
                "Other Income",
                "Other Income",
                AccountType.INCOME,
                AccountSubType.NON_OPERATING_INCOME,
                "4000",
                True,
            ),
            (
                "4910",
                "Interest Income",
                "Interest Income",
                AccountType.INCOME,
                AccountSubType.NON_OPERATING_INCOME,
                "4900",
                True,
            ),
            # EXPENSES
            (
                "5000",
                "COST OF SERVICES",
                "Cost of Services",
                AccountType.EXPENSES,
                AccountSubType.OPERATING_EXPENSES,
                None,
                True,
            ),
            (
                "5100",
                "Medical Supplies Cost",
                "Medical Supplies Cost",
                AccountType.EXPENSES,
                AccountSubType.OPERATING_EXPENSES,
                "5000",
                True,
            ),
            (
                "5110",
                "Pharmaceutical Cost",
                "Pharmaceutical Cost",
                AccountType.EXPENSES,
                AccountSubType.OPERATING_EXPENSES,
                "5000",
                True,
            ),
            (
                "5120",
                "Equipment Cost",
                "Equipment Cost",
                AccountType.EXPENSES,
                AccountSubType.OPERATING_EXPENSES,
                "5000",
                True,
            ),
            # Operating Expenses
            (
                "6000",
                "OPERATING EXPENSES",
                "Operating Expenses",
                AccountType.EXPENSES,
                AccountSubType.OPERATING_EXPENSES,
                None,
                True,
            ),
            (
                "6100",
                "Utilities Expense",
                "Utilities Expense",
                AccountType.EXPENSES,
                AccountSubType.OPERATING_EXPENSES,
                "6000",
                True,
            ),
            (
                "6200",
                "Rent Expense",
                "Rent Expense",
                AccountType.EXPENSES,
                AccountSubType.OPERATING_EXPENSES,
                "6000",
                True,
            ),
            (
                "6300",
                "Salary Expense",
                "Salary Expense",
                AccountType.EXPENSES,
                AccountSubType.OPERATING_EXPENSES,
                "6000",
                True,
            ),
            (
                "6310",
                "PF Expense",
                "Provident Fund Expense",
                AccountType.EXPENSES,
                AccountSubType.OPERATING_EXPENSES,
                "6000",
                True,
            ),
            (
                "6320",
                "ESI Expense",
                "ESI Expense",
                AccountType.EXPENSES,
                AccountSubType.OPERATING_EXPENSES,
                "6000",
                True,
            ),
            (
                "6400",
                "Professional Fees",
                "Professional Fees",
                AccountType.EXPENSES,
                AccountSubType.OPERATING_EXPENSES,
                "6000",
                True,
            ),
            (
                "6500",
                "Maintenance Expense",
                "Maintenance Expense",
                AccountType.EXPENSES,
                AccountSubType.OPERATING_EXPENSES,
                "6000",
                True,
            ),
            (
                "6600",
                "Insurance Expense",
                "Insurance Expense",
                AccountType.EXPENSES,
                AccountSubType.OPERATING_EXPENSES,
                "6000",
                True,
            ),
            (
                "6700",
                "Marketing Expense",
                "Marketing Expense",
                AccountType.EXPENSES,
                AccountSubType.OPERATING_EXPENSES,
                "6000",
                True,
            ),
            # Administrative Expenses
            (
                "6800",
                "Administrative Expenses",
                "Administrative Expenses",
                AccountType.EXPENSES,
                AccountSubType.ADMINISTRATIVE_EXPENSES,
                "6000",
                True,
            ),
            (
                "6810",
                "Office Supplies",
                "Office Supplies",
                AccountType.EXPENSES,
                AccountSubType.ADMINISTRATIVE_EXPENSES,
                "6800",
                True,
            ),
            (
                "6820",
                "Communication Expense",
                "Communication Expense",
                AccountType.EXPENSES,
                AccountSubType.ADMINISTRATIVE_EXPENSES,
                "6800",
                True,
            ),
            (
                "6830",
                "Legal & Professional",
                "Legal & Professional",
                AccountType.EXPENSES,
                AccountSubType.ADMINISTRATIVE_EXPENSES,
                "6800",
                True,
            ),
            # Depreciation and Other
            (
                "6900",
                "Depreciation Expense",
                "Depreciation Expense",
                AccountType.EXPENSES,
                AccountSubType.OPERATING_EXPENSES,
                "6000",
                True,
            ),
            (
                "6950",
                "Interest Expense",
                "Interest Expense",
                AccountType.EXPENSES,
                AccountSubType.FINANCIAL_EXPENSES,
                "6000",
                True,
            ),
            (
                "6990",
                "Other Expenses",
                "Other Expenses",
                AccountType.EXPENSES,
                AccountSubType.OPERATING_EXPENSES,
                "6000",
                True,
            ),
        ]

        created_count = 0
        for account_data in accounts_data:
            (
                account_code,
                account_name,
                description,
                account_type,
                account_subtype,
                parent_code,
                is_system,
            ) = account_data

            parent_account = None
            if parent_code:
                try:
                    parent_account = ChartOfAccounts.objects.get(
                        hospital=hospital, account_code=parent_code
                    )
                except ChartOfAccounts.DoesNotExist:
                    self.stdout.write(
                        self.style.WARNING(
                            f"Parent account {parent_code} not found for {account_code}"  # noqa: E501      # noqa: E501
                        )
                    )
                    continue

            account, created = ChartOfAccounts.objects.get_or_create(
                hospital=hospital,
                account_code=account_code,
                defaults={
                    "account_name": account_name,
                    "account_type": account_type,
                    "account_subtype": account_subtype,
                    "parent_account": parent_account,
                    "description": description,
                    "is_system_account": is_system,
                    "is_active": True,
                },
            )

            if created:
                created_count += 1
                self.stdout.write(
                    f"  Created account: {account_code} - {account_name}"
                )  # noqa: E501

        self.stdout.write(
            self.style.SUCCESS(
                f"Created {created_count} accounts for {hospital.name}"
            )  # noqa: E501
        )
