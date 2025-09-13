from datetime import datetime, timedelta
from decimal import Decimal

from billing.models import ServiceCatalog
from django.db.models import Count, Q, Sum
from django.utils import timezone
from hospitals.models import Hospital
from patients.models import Patient
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from users.models import User

from .models import (
    GlobalSettings,
    HospitalSubscription,
    ModulePermission,
    SubscriptionTier,
    SuperadminUser,
    SystemAlert,
    TierModuleAccess,
    UsageMetrics,
)
from .serializers import (
    DashboardStatsSerializer,
    GlobalSettingsSerializer,
    HospitalSubscriptionSerializer,
    HospitalSummarySerializer,
    ModulePermissionSerializer,
    PriceEstimatorRequestSerializer,
    PriceEstimatorResponseSerializer,
    SubscriptionTierSerializer,
    SuperadminUserSerializer,
    SystemAlertSerializer,
    UsageMetricsSerializer,
)


class SuperadminPermission(permissions.BasePermission):
    """Custom permission for superadmin users"""

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False

        # Check if user has superadmin profile
        try:
            superadmin = request.user.superadmin_profile
            return superadmin.is_active
        except SuperadminUser.DoesNotExist:
            return False


class SubscriptionTierViewSet(viewsets.ModelViewSet):
    queryset = SubscriptionTier.objects.all()
    serializer_class = SubscriptionTierSerializer
    permission_classes = [SuperadminPermission]

    @action(detail=True, methods=["post"])
    def clone(self, request, pk=None):
        """Clone a subscription tier"""
        tier = self.get_object()
        new_tier = SubscriptionTier.objects.create(
            name=f"{tier.name} (Copy)",
            tier_type=tier.tier_type,
            description=tier.description,
            price_monthly=tier.price_monthly,
            price_yearly=tier.price_yearly,
            max_users=tier.max_users,
            max_beds=tier.max_beds,
            storage_gb=tier.storage_gb,
            api_calls_per_month=tier.api_calls_per_month,
            support_level=tier.support_level,
            is_active=False,  # Clones start as inactive
        )

        # Clone module access
        for access in tier.module_access.all():
            TierModuleAccess.objects.create(
                tier=new_tier,
                module=access.module,
                is_enabled=access.is_enabled,
                feature_limits=access.feature_limits,
            )

        serializer = self.get_serializer(new_tier)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class HospitalSubscriptionViewSet(viewsets.ModelViewSet):
    queryset = HospitalSubscription.objects.select_related("hospital", "tier")
    serializer_class = HospitalSubscriptionSerializer
    permission_classes = [SuperadminPermission]
    filterset_fields = ["status", "tier", "billing_cycle"]
    search_fields = ["hospital__name", "billing_contact_name"]
    ordering_fields = ["created_at", "end_date", "monthly_amount"]
    ordering = ["-created_at"]

    @action(detail=False, methods=["get"])
    def overview(self, request):
        """Get subscription overview statistics"""
        subscriptions = self.get_queryset()

        stats = {
            "total": subscriptions.count(),
            "active": subscriptions.filter(status="ACTIVE").count(),
            "trial": subscriptions.filter(status="TRIAL").count(),
            "expired": subscriptions.filter(status="EXPIRED").count(),
            "suspended": subscriptions.filter(status="SUSPENDED").count(),
            "total_revenue": subscriptions.filter(status="ACTIVE").aggregate(
                total=Sum("monthly_amount")
            )["total"]
            or 0,
            "expiring_soon": subscriptions.filter(
                end_date__lte=timezone.now() + timedelta(days=7)
            ).count(),
        }

        return Response(stats)

    @action(detail=True, methods=["post"])
    def extend_subscription(self, request, pk=None):
        """Extend subscription by specified days"""
        subscription = self.get_object()
        days = request.data.get("days", 30)

        subscription.end_date += timedelta(days=days)
        subscription.save()

        return Response(
            {
                "message": f"Subscription extended by {days} days",
                "new_end_date": subscription.end_date,
            }
        )

    @action(detail=True, methods=["post"])
    def change_tier(self, request, pk=None):
        """Change subscription tier"""
        subscription = self.get_object()
        new_tier_id = request.data.get("tier_id")

        try:
            new_tier = SubscriptionTier.objects.get(id=new_tier_id)
            old_tier = subscription.tier

            subscription.tier = new_tier
            subscription.monthly_amount = new_tier.price_monthly
            subscription.save()

            return Response(
                {
                    "message": f"Tier changed from {old_tier.name} to {new_tier.name}",
                    "old_tier": old_tier.name,
                    "new_tier": new_tier.name,
                }
            )
        except SubscriptionTier.DoesNotExist:
            return Response(
                {"error": "Invalid tier ID"}, status=status.HTTP_400_BAD_REQUEST
            )


class SuperadminDashboardViewSet(viewsets.ViewSet):
    permission_classes = [SuperadminPermission]

    @action(detail=False, methods=["get"])
    def stats(self, request):
        """Get comprehensive dashboard statistics"""
        # Basic counts
        total_hospitals = Hospital.objects.count()
        total_users = User.objects.count()
        total_patients = Patient.objects.count()

        # Subscription stats
        subscriptions = HospitalSubscription.objects.all()
        active_subscriptions = subscriptions.filter(status="ACTIVE").count()
        trial_subscriptions = subscriptions.filter(status="TRIAL").count()
        expired_subscriptions = subscriptions.filter(status="EXPIRED").count()

        # Revenue calculation
        total_revenue_monthly = subscriptions.filter(status="ACTIVE").aggregate(
            total=Sum("monthly_amount")
        )["total"] or Decimal("0")

        # System health check
        active_alerts = SystemAlert.objects.filter(
            is_active=True,
            show_from__lte=timezone.now(),
            show_until__gte=timezone.now(),
        ).count()

        system_health = "Excellent"
        if active_alerts > 0:
            critical_alerts = SystemAlert.objects.filter(
                is_active=True,
                severity="CRITICAL",
                show_from__lte=timezone.now(),
                show_until__gte=timezone.now(),
            ).count()
            if critical_alerts > 0:
                system_health = "Critical"
            else:
                system_health = "Warning"

        stats = {
            "total_hospitals": total_hospitals,
            "active_subscriptions": active_subscriptions,
            "trial_subscriptions": trial_subscriptions,
            "expired_subscriptions": expired_subscriptions,
            "total_revenue_monthly": total_revenue_monthly,
            "total_users": total_users,
            "total_patients": total_patients,
            "active_alerts": active_alerts,
            "system_health": system_health,
        }

        serializer = DashboardStatsSerializer(stats)
        return Response(serializer.data)

    @action(detail=False, methods=["get"])
    def hospitals(self, request):
        """Get hospital overview with subscription details"""
        hospitals = Hospital.objects.select_related("subscription__tier").all()
        serializer = HospitalSummarySerializer(hospitals, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=["get"])
    def recent_activity(self, request):
        """Get recent system activity"""
        # Recent hospitals
        recent_hospitals = Hospital.objects.order_by("-created_at")[:5]

        # Recent alerts
        recent_alerts = SystemAlert.objects.order_by("-created_at")[:5]

        # Usage metrics for last 7 days
        week_ago = timezone.now().date() - timedelta(days=7)
        usage_metrics = UsageMetrics.objects.filter(date__gte=week_ago).order_by(
            "-date"
        )[:10]

        return Response(
            {
                "recent_hospitals": HospitalSummarySerializer(
                    recent_hospitals, many=True
                ).data,
                "recent_alerts": SystemAlertSerializer(recent_alerts, many=True).data,
                "usage_metrics": UsageMetricsSerializer(usage_metrics, many=True).data,
            }
        )

    @action(detail=False, methods=["post"])
    def price_estimator(self, request):
        """Quick price estimation tool"""
        serializer = PriceEstimatorRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data
        services = data["services"]
        patient_type = data["patient_type"]
        insurance_type = data.get("insurance_type", "NONE")
        room_type = data.get("room_type", "GENERAL")
        duration_days = data.get("duration_days", 1)

        # Calculate base costs
        total_estimate = Decimal("0")
        breakdown = []

        # Service costs
        for service in services:
            service_name = service.get("name", "")
            quantity = int(service.get("quantity", 1))

            # Try to find service in catalog
            try:
                catalog_item = ServiceCatalog.objects.filter(
                    name__icontains=service_name
                ).first()

                if catalog_item:
                    cost = catalog_item.price_cents / 100 * quantity
                else:
                    # Default pricing for common services
                    default_prices = {
                        "consultation": 500,
                        "blood_test": 200,
                        "xray": 800,
                        "ct_scan": 3000,
                        "mri": 8000,
                        "surgery": 25000,
                        "room_charge": 1000,
                    }

                    cost = (
                        Decimal(str(default_prices.get("consultation", 500))) * quantity
                    )

                total_estimate += cost
                breakdown.append(
                    {
                        "service": service_name,
                        "quantity": quantity,
                        "unit_cost": float(cost / quantity),
                        "total_cost": float(cost),
                    }
                )
            except Exception:
                # Fallback pricing
                cost = Decimal("500") * quantity
                total_estimate += cost
                breakdown.append(
                    {
                        "service": service_name,
                        "quantity": quantity,
                        "unit_cost": 500.0,
                        "total_cost": float(cost),
                    }
                )

        # Room charges for IPD
        if patient_type == "IPD":
            room_charges = {
                "GENERAL": 1000,
                "PRIVATE": 2500,
                "DELUXE": 4000,
                "SUITE": 8000,
            }
            room_cost = Decimal(str(room_charges[room_type])) * duration_days
            total_estimate += room_cost
            breakdown.append(
                {
                    "service": f"{room_type.title()} Room ({duration_days} days)",
                    "quantity": duration_days,
                    "unit_cost": float(room_cost / duration_days),
                    "total_cost": float(room_cost),
                }
            )

        # Insurance coverage calculation
        insurance_coverage = Decimal("0")
        if insurance_type == "BASIC":
            insurance_coverage = total_estimate * Decimal("0.6")  # 60% coverage
        elif insurance_type == "PREMIUM":
            insurance_coverage = total_estimate * Decimal("0.8")  # 80% coverage

        patient_responsibility = total_estimate - insurance_coverage

        # Discount calculations
        discount_available = Decimal("0")
        estimated_savings = Decimal("0")

        if patient_type == "IPD" and duration_days > 5:
            discount_available = total_estimate * Decimal("0.1")  # 10% for long stay
            estimated_savings = discount_available

        response_data = {
            "total_estimate": total_estimate,
            "breakdown": breakdown,
            "insurance_coverage": insurance_coverage,
            "patient_responsibility": patient_responsibility,
            "discount_available": discount_available,
            "estimated_savings": estimated_savings,
        }

        response_serializer = PriceEstimatorResponseSerializer(response_data)
        return Response(response_serializer.data)


class SystemAlertViewSet(viewsets.ModelViewSet):
    queryset = SystemAlert.objects.all()
    serializer_class = SystemAlertSerializer
    permission_classes = [SuperadminPermission]
    ordering = ["-created_at"]

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    @action(detail=False, methods=["get"])
    def active(self, request):
        """Get currently active alerts"""
        now = timezone.now()
        active_alerts = (
            self.get_queryset()
            .filter(is_active=True, show_from__lte=now)
            .filter(Q(show_until__isnull=True) | Q(show_until__gte=now))
        )

        serializer = self.get_serializer(queryset=active_alerts, many=True)
        return Response(serializer.data)


class GlobalSettingsViewSet(viewsets.ModelViewSet):
    queryset = GlobalSettings.objects.all()
    serializer_class = GlobalSettingsSerializer
    permission_classes = [SuperadminPermission]
    filterset_fields = ["category"]
    search_fields = ["key", "description"]

    def perform_update(self, serializer):
        serializer.save(last_modified_by=self.request.user)

    def perform_create(self, serializer):
        serializer.save(last_modified_by=self.request.user)


class UsageMetricsViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = UsageMetrics.objects.select_related("hospital")
    serializer_class = UsageMetricsSerializer
    permission_classes = [SuperadminPermission]
    filterset_fields = ["hospital", "date"]
    ordering = ["-date"]

    @action(detail=False, methods=["get"])
    def trends(self, request):
        """Get usage trends over time"""
        days = int(request.query_params.get("days", 30))
        start_date = timezone.now().date() - timedelta(days=days)

        metrics = self.get_queryset().filter(date__gte=start_date)

        # Aggregate by date
        daily_stats = {}
        for metric in metrics:
            date_str = metric.date.strftime("%Y-%m-%d")
            if date_str not in daily_stats:
                daily_stats[date_str] = {
                    "date": date_str,
                    "total_users": 0,
                    "total_api_calls": 0,
                    "total_patients_created": 0,
                    "total_storage_used": 0,
                }

            daily_stats[date_str]["total_users"] += metric.active_users
            daily_stats[date_str]["total_api_calls"] += metric.api_calls
            daily_stats[date_str]["total_patients_created"] += metric.patients_created
            daily_stats[date_str]["total_storage_used"] += metric.storage_used_mb

        return Response(list(daily_stats.values()))
