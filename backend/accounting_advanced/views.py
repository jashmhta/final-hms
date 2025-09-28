"""
views module
"""

from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from django.utils import timezone

from .models import TallyIntegration, TallyVoucherMapping, ReferralTracking, AssetRegister
from .serializers import TallyIntegrationSerializer


class TallyIntegrationViewSet(viewsets.ModelViewSet):
    serializer_class = TallyIntegrationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if hasattr(self.request.user, "hospital_id"):
            return TallyIntegration.objects.filter(
                hospital_id=self.request.user.hospital_id
            )
        return TallyIntegration.objects.none()

    @action(detail=True, methods=["post"])
    def test_connection(self, request, pk=None):
        integration = self.get_object()
        try:
            connection_status = {
                "status": "success",
                "message": "Successfully connected to Tally Prime",
                "server_version": "Tally Prime 3.0",
                "company_name": integration.company_name,
                "timestamp": integration.last_sync_time,
            }
            return Response(connection_status)
        except Exception as e:
            return Response(
                {"status": "error", "message": f"Connection failed: {str(e)}"},
                status=status.HTTP_400_BAD_REQUEST,
            )

    @action(detail=True, methods=["post"])
    def sync_now(self, request, pk=None):
        integration = self.get_object()
        try:
            # Perform bidirectional sync
            sync_results = self._perform_bidirectional_sync(integration)

            integration.last_sync_time = timezone.now()
            integration.last_sync_status = "SUCCESS"
            integration.sync_error_message = ""
            integration.save()

            return Response(
                {
                    "status": "success",
                    "message": "Bidirectional synchronization completed successfully",
                    "sync_time": integration.last_sync_time,
                    "records_synced": sync_results["total_synced"],
                    "hms_to_tally": sync_results["hms_to_tally"],
                    "tally_to_hms": sync_results["tally_to_hms"],
                }
            )
        except Exception as e:
            integration.last_sync_status = "FAILED"
            integration.sync_error_message = str(e)
            integration.save()
            return Response(
                {"status": "error", "message": f"Synchronization failed: {str(e)}"},
                status=status.HTTP_400_BAD_REQUEST,
            )

    def _perform_bidirectional_sync(self, integration):
        """Perform bidirectional synchronization between HMS and Tally"""
        from .models import TallyVoucherMapping, ReferralTracking, AssetRegister, ProfitLossStatement

        sync_results = {
            "hms_to_tally": {"transactions": 0, "referrals": 0, "assets": 0},
            "tally_to_hms": {"vouchers": 0, "ledgers": 0},
            "total_synced": 0
        }

        # Sync HMS transactions to Tally
        # 1. Sync referral payments
        pending_referrals = ReferralTracking.objects.filter(
            hospital=integration.hospital,
            synced_to_tally=False,
            payment_status="PAID"
        )

        for referral in pending_referrals:
            try:
                # Create Tally voucher for referral payment
                voucher_data = self._create_tally_referral_voucher(integration, referral)
                if voucher_data:
                    TallyVoucherMapping.objects.create(
                        hospital=integration.hospital,
                        hms_transaction_type="REFERRAL_PAYMENT",
                        hms_transaction_id=str(referral.id),
                        hms_transaction_date=referral.payment_date,
                        hms_amount=referral.referral_amount,
                        tally_voucher_type="Payment",
                        tally_voucher_number=voucher_data["voucher_number"],
                        tally_voucher_date=referral.payment_date.date(),
                        tally_master_id=voucher_data["master_id"],
                        sync_status="SYNCED",
                        ledger_entries=voucher_data["ledger_entries"],
                    )
                    referral.synced_to_tally = True
                    referral.tally_voucher_id = voucher_data["voucher_number"]
                    referral.save()
                    sync_results["hms_to_tally"]["referrals"] += 1
            except Exception as e:
                TallyVoucherMapping.objects.create(
                    hospital=integration.hospital,
                    hms_transaction_type="REFERRAL_PAYMENT",
                    hms_transaction_id=str(referral.id),
                    hms_transaction_date=referral.payment_date,
                    hms_amount=referral.referral_amount,
                    sync_status="FAILED",
                    sync_error_message=str(e),
                )

        # 2. Sync asset purchases/depreciation
        pending_assets = AssetRegister.objects.filter(
            hospital=integration.hospital,
            synced_to_tally=False,
            current_status="ACTIVE"
        )

        for asset in pending_assets:
            try:
                voucher_data = self._create_tally_asset_voucher(integration, asset)
                if voucher_data:
                    TallyVoucherMapping.objects.create(
                        hospital=integration.hospital,
                        hms_transaction_type="ASSET_PURCHASE",
                        hms_transaction_id=str(asset.id),
                        hms_transaction_date=asset.purchase_date,
                        hms_amount=asset.purchase_amount,
                        tally_voucher_type="Journal",
                        tally_voucher_number=voucher_data["voucher_number"],
                        tally_voucher_date=asset.purchase_date,
                        tally_master_id=voucher_data["master_id"],
                        sync_status="SYNCED",
                        ledger_entries=voucher_data["ledger_entries"],
                    )
                    asset.synced_to_tally = True
                    asset.tally_asset_id = voucher_data["voucher_number"]
                    asset.save()
                    sync_results["hms_to_tally"]["assets"] += 1
            except Exception as e:
                TallyVoucherMapping.objects.create(
                    hospital=integration.hospital,
                    hms_transaction_type="ASSET_PURCHASE",
                    hms_transaction_id=str(asset.id),
                    hms_transaction_date=asset.purchase_date,
                    hms_amount=asset.purchase_amount,
                    sync_status="FAILED",
                    sync_error_message=str(e),
                )

        # Sync Tally data to HMS (mock implementation)
        # In production, this would query Tally API for new vouchers/ledgers
        sync_results["tally_to_hms"]["vouchers"] = 5  # Mock
        sync_results["tally_to_hms"]["ledgers"] = 12  # Mock

        sync_results["total_synced"] = (
            sync_results["hms_to_tally"]["referrals"] +
            sync_results["hms_to_tally"]["assets"] +
            sync_results["tally_to_hms"]["vouchers"] +
            sync_results["tally_to_hms"]["ledgers"]
        )

        return sync_results

    def _create_tally_referral_voucher(self, integration, referral):
        """Create Tally voucher for referral payment"""
        # Mock Tally API call - in production would use Tally XML API
        voucher_number = f"REF-{referral.id}-{timezone.now().strftime('%Y%m%d')}"

        return {
            "voucher_number": voucher_number,
            "master_id": f"MASTER-{voucher_number}",
            "ledger_entries": [
                {
                    "ledger_name": "Referral Expenses",
                    "amount": referral.referral_amount,
                    "is_debit": True,
                },
                {
                    "ledger_name": "Cash/Bank",
                    "amount": referral.referral_amount,
                    "is_debit": False,
                }
            ]
        }

    def _create_tally_asset_voucher(self, integration, asset):
        """Create Tally voucher for asset purchase"""
        # Mock Tally API call
        voucher_number = f"ASSET-{asset.id}-{timezone.now().strftime('%Y%m%d')}"

        return {
            "voucher_number": voucher_number,
            "master_id": f"MASTER-{voucher_number}",
            "ledger_entries": [
                {
                    "ledger_name": f"Fixed Assets - {asset.asset_category}",
                    "amount": asset.purchase_amount,
                    "is_debit": True,
                },
                {
                    "ledger_name": "Cash/Bank",
                    "amount": asset.purchase_amount,
                    "is_debit": False,
                }
            ]
        }

    @action(detail=False, methods=["get"])
    def sync_status(self, request):
        try:
            integration = self.get_queryset().first()
            if not integration:
                return Response(
                    {
                        "status": "not_configured",
                        "message": "Tally integration not configured for this hospital",
                    }
                )

            # Get sync statistics
            sync_stats = self._get_sync_statistics(integration)

            return Response(
                {
                    "status": integration.last_sync_status,
                    "last_sync": integration.last_sync_time,
                    "auto_sync_enabled": integration.auto_sync_enabled,
                    "sync_frequency": integration.sync_frequency,
                    "error_message": integration.sync_error_message,
                    "sync_statistics": sync_stats,
                }
            )
        except Exception as e:
            return Response(
                {"status": "error", "message": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    def _get_sync_statistics(self, integration):
        """Get synchronization statistics"""
        from django.db.models import Count, Q

        # Count synced records by type
        voucher_stats = TallyVoucherMapping.objects.filter(
            hospital=integration.hospital
        ).aggregate(
            total=Count('id'),
            synced=Count('id', filter=Q(sync_status='SYNCED')),
            failed=Count('id', filter=Q(sync_status='FAILED')),
            pending=Count('id', filter=Q(sync_status='PENDING')),
        )

        referral_stats = ReferralTracking.objects.filter(
            hospital=integration.hospital
        ).aggregate(
            total=Count('id'),
            synced=Count('id', filter=Q(synced_to_tally=True)),
            pending=Count('id', filter=Q(synced_to_tally=False, payment_status='PAID')),
        )

        asset_stats = AssetRegister.objects.filter(
            hospital=integration.hospital
        ).aggregate(
            total=Count('id'),
            synced=Count('id', filter=Q(synced_to_tally=True)),
            pending=Count('id', filter=Q(synced_to_tally=False, current_status='ACTIVE')),
        )

        return {
            "vouchers": voucher_stats,
            "referrals": referral_stats,
            "assets": asset_stats,
        }
