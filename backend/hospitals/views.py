from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle

from core.enhanced_cache import cache_result, enhanced_cache
from core.permissions import ModuleEnabledPermission
from core.utils import get_object_or_404, paginated_response

from .models import Hospital, HospitalPlan, Plan
from .serializers import HospitalPlanSerializer, HospitalSerializer, PlanSerializer
from .utils import generate_hospital_code, validate_hospital_data


class IsSuperAdmin(IsAuthenticated):
    def has_permission(self, request, view):
        base = super().has_permission(request, view)
        return base and (request.user.is_superuser or getattr(request.user, "role", None) == "SUPER_ADMIN")


class HospitalViewSet(viewsets.ModelViewSet):
    serializer_class = HospitalSerializer
    queryset = Hospital.objects.all()
    permission_classes = [IsAuthenticated, ModuleEnabledPermission]
    lookup_field = 'code'
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = 'hospital_operations'
    filterset_fields = ['status', 'country', 'city']
    search_fields = ['name', 'code', 'city', 'country']
    ordering_fields = ['name', 'created_at', 'updated_at']
    required_module = 'enable_hospitals'

    def get_queryset(self):
        user = self.request.user
        qs = super().get_queryset().select_related('plan').prefetch_related('departments')
        if user.is_superuser or getattr(user, 'role', None) == 'SUPER_ADMIN':
            return qs
        if getattr(user, 'hospital_id', None):
            return qs.filter(id=user.hospital_id)
        return qs.none()

    def perform_create(self, serializer):
        user = self.request.user
        if not (user.is_superuser or getattr(user, 'role', None) == 'SUPER_ADMIN'):
            raise PermissionDenied("Only super admin can create hospitals")

        # Validate hospital data
        validate_hospital_data(serializer.validated_data)

        # Generate hospital code if not provided
        hospital_code = serializer.validated_data.get('code')
        if not hospital_code:
            hospital_code = generate_hospital_code(serializer.validated_data['name'])
            serializer.validated_data['code'] = hospital_code

        hospital = serializer.save()

        # Log creation
        from core.models import AuditLog
        AuditLog.objects.create(
            user=user,
            action='CREATE',
            model='Hospital',
            object_id=hospital.id,
            details=f'Created hospital: {hospital.name}'
        )
        return hospital

    def perform_update(self, serializer):
        instance = self.get_object()
        user = self.request.user

        if not (user.is_superuser or getattr(user, 'role', None) == 'SUPER_ADMIN'):
            raise PermissionDenied("Only super admin can update hospitals")

        # Validate hospital data
        validate_hospital_data(serializer.validated_data)

        hospital = serializer.save()

        # Log update
        from core.models import AuditLog
        AuditLog.objects.create(
            user=user,
            action='UPDATE',
            model='Hospital',
            object_id=hospital.id,
            details=f'Updated hospital: {hospital.name}'
        )

        # Invalidate cache
        enhanced_cache.invalidate_by_tag(f'hospital_{hospital.code}')
        return hospital

    def perform_destroy(self, instance):
        user = self.request.user
        if not (user.is_superuser or getattr(user, 'role', None) == 'SUPER_ADMIN'):
            raise PermissionDenied("Only super admin can delete hospitals")

        # Check if hospital has associated data
        if instance.patients.exists() or instance.users.exists():
            raise PermissionDenied("Cannot delete hospital with associated patients or users")

        # Log deletion
        from core.models import AuditLog
        AuditLog.objects.create(
            user=user,
            action='DELETE',
            model='Hospital',
            object_id=instance.id,
            details=f'Deleted hospital: {instance.name}'
        )

        # Invalidate cache
        enhanced_cache.invalidate_by_tag(f'hospital_{instance.code}')

        instance.delete()

    @action(detail=False, methods=['get'])
    @cache_result(timeout=300, key_prefix='hospital_stats', tags=['analytics_data'])
    def stats(self, request):
        """Get hospital statistics"""
        from django.db.models import Count
        from patients.models import Patient

        user = request.user
        if user.is_superuser or getattr(user, 'role', None) == 'SUPER_ADMIN':
            hospitals = Hospital.objects.all()
        else:
            hospitals = Hospital.objects.filter(id=user.hospital_id) if user.hospital_id else Hospital.objects.none()

        stats = []
        for hospital in hospitals:
            patient_count = Patient.objects.filter(hospital=hospital).count()
            stats.append({
                'hospital': HospitalSerializer(hospital).data,
                'patient_count': patient_count,
                'status': hospital.status,
            })

        return Response({'stats': stats})

    @action(detail=True, methods=['post'])
    def activate(self, request, code=None):
        """Activate hospital"""
        hospital = self.get_object()
        hospital.status = 'ACTIVE'
        hospital.save()

        # Log activation
        from core.models import AuditLog
        AuditLog.objects.create(
            user=request.user,
            action='UPDATE',
            model='Hospital',
            object_id=hospital.id,
            details=f'Activated hospital: {hospital.name}'
        )

        return Response({'message': 'Hospital activated successfully'})

    @action(detail=True, methods=['post'])
    def deactivate(self, request, code=None):
        """Deactivate hospital"""
        hospital = self.get_object()
        hospital.status = 'INACTIVE'
        hospital.save()

        # Log deactivation
        from core.models import AuditLog
        AuditLog.objects.create(
            user=request.user,
            action='UPDATE',
            model='Hospital',
            object_id=hospital.id,
            details=f'Deactivated hospital: {hospital.name}'
        )

        return Response({'message': 'Hospital deactivated successfully'})

    @action(detail=True, methods=['get'])
    def utilization(self, request, code=None):
        """Get hospital utilization statistics"""
        hospital = self.get_object()
        utilization_data = calculate_hospital_utilization(hospital.id)
        return Response(utilization_data)

    @action(detail=True, methods=['get'])
    def performance(self, request, code=None):
        """Get hospital performance metrics"""
        days = int(request.query_params.get('days', 30))
        hospital = self.get_object()
        performance_data = get_hospital_performance_metrics(hospital.id, days)
        return Response(performance_data)


class PlanViewSet(viewsets.ModelViewSet):
    serializer_class = PlanSerializer
    queryset = Plan.objects.all()
    permission_classes = [IsSuperAdmin, ModuleEnabledPermission]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = 'plan_operations'
    filterset_fields = ['is_active', 'tier']
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'price', 'created_at']
    required_module = 'enable_hospitals'

    def perform_create(self, serializer):
        plan = serializer.save()

        # Log creation
        from core.models import AuditLog
        AuditLog.objects.create(
            user=self.request.user,
            action='CREATE',
            model='Plan',
            object_id=plan.id,
            details=f'Created plan: {plan.name}'
        )
        return plan

    def perform_update(self, serializer):
        instance = self.get_object()
        plan = serializer.save()

        # Log update
        from core.models import AuditLog
        AuditLog.objects.create(
            user=self.request.user,
            action='UPDATE',
            model='Plan',
            object_id=plan.id,
            details=f'Updated plan: {plan.name}'
        )
        return plan

    def perform_destroy(self, instance):
        # Check if plan is in use
        if instance.hospital_plans.exists():
            raise PermissionDenied("Cannot delete plan that is in use")

        # Log deletion
        from core.models import AuditLog
        AuditLog.objects.create(
            user=self.request.user,
            action='DELETE',
            model='Plan',
            object_id=instance.id,
            details=f'Deleted plan: {instance.name}'
        )

        instance.delete()

    @action(detail=True, methods=['post'])
    def activate(self, request, pk=None):
        """Activate plan"""
        plan = self.get_object()
        plan.is_active = True
        plan.save()
        return Response({'message': 'Plan activated successfully'})

    @action(detail=True, methods=['post'])
    def deactivate(self, request, pk=None):
        """Deactivate plan"""
        plan = self.get_object()
        plan.is_active = False
        plan.save()
        return Response({'message': 'Plan deactivated successfully'})

    @action(detail=True, methods=['get'])
    def hospitals(self, request, pk=None):
        """Get hospitals subscribed to this plan"""
        plan = self.get_object()
        hospitals_data = get_hospitals_by_plan(plan.id)
        return Response({'hospitals': hospitals_data})


class HospitalPlanViewSet(viewsets.ModelViewSet):
    serializer_class = HospitalPlanSerializer
    queryset = HospitalPlan.objects.select_related('hospital', 'plan').all()
    permission_classes = [IsSuperAdmin, ModuleEnabledPermission]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = 'hospital_plan_operations'
    filterset_fields = ['hospital', 'plan', 'is_active']
    search_fields = ['hospital__name', 'plan__name']
    ordering_fields = ['start_date', 'end_date', 'created_at']
    required_module = 'enable_hospitals'

    def perform_create(self, serializer):
        # Validate hospital plan data
        validate_hospital_plan_data(serializer.validated_data)

        hospital_plan = serializer.save()

        # Log creation
        from core.models import AuditLog
        AuditLog.objects.create(
            user=self.request.user,
            action='CREATE',
            model='HospitalPlan',
            object_id=hospital_plan.id,
            details=f'Created hospital plan: {hospital_plan.hospital.name} - {hospital_plan.plan.name}'
        )
        return hospital_plan

    def perform_update(self, serializer):
        instance = self.get_object()

        # Validate hospital plan data
        validate_hospital_plan_data(serializer.validated_data)

        hospital_plan = serializer.save()

        # Log update
        from core.models import AuditLog
        AuditLog.objects.create(
            user=self.request.user,
            action='UPDATE',
            model='HospitalPlan',
            object_id=hospital_plan.id,
            details=f'Updated hospital plan: {hospital_plan.hospital.name} - {hospital_plan.plan.name}'
        )
        return hospital_plan

    @action(detail=True, methods=['post'])
    def renew(self, request, pk=None):
        """Renew hospital plan"""
        hospital_plan = self.get_object()

        # Calculate new end date
        from datetime import timedelta
        duration = hospital_plan.plan.duration_months
        new_end_date = hospital_plan.end_date + timedelta(days=duration * 30)

        hospital_plan.end_date = new_end_date
        hospital_plan.save()

        return Response({
            'message': 'Hospital plan renewed successfully',
            'new_end_date': new_end_date
        })

    @action(detail=True, methods=['post'])
    def activate(self, request, pk=None):
        """Activate hospital plan"""
        hospital_plan = self.get_object()
        hospital_plan.is_active = True
        hospital_plan.save()
        return Response({'message': 'Hospital plan activated successfully'})

    @action(detail=True, methods=['post'])
    def deactivate(self, request, pk=None):
        """Deactivate hospital plan"""
        hospital_plan = self.get_object()
        hospital_plan.is_active = False
        hospital_plan.save()
        return Response({'message': 'Hospital plan deactivated successfully'})


