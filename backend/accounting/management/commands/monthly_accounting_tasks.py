from datetime import datetime

from django.core.management.base import BaseCommand
from django.utils import timezone

from accounting.models import FinancialYear
from accounting.utils import DepreciationCalculator
from hospitals.models import Hospital


class Command(BaseCommand):
    help = "Run monthly accounting tasks like depreciation processing"

    def add_arguments(self, parser):
        parser.add_argument(
            "--hospital-id",
            type=int,
            help="Hospital ID to process (optional - if not provided, processes all)",
        )
        parser.add_argument(
            "--date",
            type=str,
            help="Processing date in YYYY-MM-DD format (optional - defaults to current date)",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show what would be processed without making changes",
        )

    def handle(self, *args, **options):
        hospital_id = options.get("hospital_id")
        processing_date_str = options.get("date")
        dry_run = options.get("dry_run", False)
        if processing_date_str:
            try:
                processing_date = datetime.strptime(processing_date_str, "%Y-%m-%d").date()
            except ValueError:
                self.stdout.write(self.style.ERROR("Invalid date format. Use YYYY-MM-DD format."))
                return
        else:
            processing_date = timezone.now().date()
        if hospital_id:
            hospitals = Hospital.objects.filter(id=hospital_id)
        else:
            hospitals = Hospital.objects.all()
        if not hospitals.exists():
            self.stdout.write(self.style.ERROR("No hospitals found to process."))
            return
        self.stdout.write(f"Processing monthly tasks for date: {processing_date}")
        if dry_run:
            self.stdout.write(self.style.WARNING("DRY RUN MODE - No changes will be made"))
        total_processed = 0
        for hospital in hospitals:
            self.stdout.write(f"Processing {hospital.name}...")
            current_fy = FinancialYear.objects.filter(
                hospital=hospital,
                start_date__lte=processing_date,
                end_date__gte=processing_date,
            ).first()
            if not current_fy:
                self.stdout.write(
                    self.style.WARNING(f"No financial year configured for {hospital.name} on {processing_date}")
                )
                continue
            if current_fy.is_locked:
                self.stdout.write(self.style.WARNING(f"Financial year is locked for {hospital.name}"))
                continue
            if not dry_run:
                processed_assets = DepreciationCalculator.process_monthly_depreciation(hospital, processing_date)
            else:
                from accounting.models import DepreciationSchedule, FixedAsset

                active_assets = FixedAsset.objects.filter(
                    hospital=hospital,
                    is_active=True,
                    purchase_date__lt=processing_date,
                )
                processed_assets = 0
                for asset in active_assets:
                    existing_entry = DepreciationSchedule.objects.filter(
                        asset=asset,
                        depreciation_date__year=processing_date.year,
                        depreciation_date__month=processing_date.month,
                    ).first()
                    if not existing_entry:
                        monthly_depreciation = DepreciationCalculator.calculate_monthly_depreciation(asset)
                        if monthly_depreciation > 0:
                            processed_assets += 1
                            self.stdout.write(
                                f"  Would process asset: {asset.asset_code} - ₹{monthly_depreciation/100:,.2f}"
                            )
            self.stdout.write(self.style.SUCCESS(f"  Processed depreciation for {processed_assets} assets"))
            total_processed += processed_assets
            self.stdout.write("  Monthly reports generation would be triggered here")
            from datetime import timedelta

            from accounting.models import ComplianceDocument

            expiring_docs = ComplianceDocument.objects.filter(
                hospital=hospital,
                is_active=True,
                expiry_date__lte=processing_date + timedelta(days=30),
                expiry_date__gte=processing_date,
            )
            if expiring_docs.exists():
                self.stdout.write(self.style.WARNING(f"  {expiring_docs.count()} compliance documents expiring soon"))
                for doc in expiring_docs:
                    days_to_expiry = (doc.expiry_date - processing_date).days
                    self.stdout.write(
                        f"    - {doc.document_type}: {doc.document_number} (expires in {days_to_expiry} days)"
                    )
        self.stdout.write(self.style.SUCCESS(f"Completed monthly tasks. Total assets processed: {total_processed}"))
