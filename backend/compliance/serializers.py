from rest_framework import serializers
from .models import (
    ConsentManagement,
    ConsentAuditLog,
    DataSubjectRequest,
    DataSubjectRequestAudit,
    ConsentType,
    ConsentStatus,
    DataRetentionPolicy,
)


class ConsentManagementSerializer(serializers.ModelSerializer):
    """
    GDPR Article 7 compliant consent management serializer
    """
    patient_name = serializers.CharField(source='patient.get_full_name', read_only=True)
    patient_id = serializers.IntegerField(source='patient.id', read_only=True)
    hospital_name = serializers.CharField(source='hospital.name', read_only=True)
    is_valid = serializers.BooleanField(read_only=True)
    days_until_expiry = serializers.IntegerField(read_only=True)

    class Meta:
        model = ConsentManagement
        fields = [
            'id', 'uuid', 'patient_name', 'patient_id', 'hospital_name',
            'consent_type', 'status', 'version', 'title', 'description',
            'purpose', 'data_categories', 'third_parties', 'retention_period',
            'consent_date', 'expiry_date', 'revoked_date', 'withdrawal_method',
            'consent_form_url', 'witness_name', 'interpreter_used',
            'interpreter_name', 'language_preference', 'is_valid',
            'days_until_expiry', 'created_by', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'uuid', 'created_by', 'created_at', 'updated_at']

    def validate(self, data):
        """
        Validate consent data
        """
        # Check expiry date is after consent date
        if data.get('consent_date') and data.get('expiry_date'):
            if data['expiry_date'] <= data['consent_date']:
                raise serializers.ValidationError("Expiry date must be after consent date")

        # Validate data categories
        data_categories = data.get('data_categories', [])
        if not isinstance(data_categories, list):
            raise serializers.ValidationError("Data categories must be a list")

        # Validate third parties
        third_parties = data.get('third_parties', [])
        if not isinstance(third_parties, list):
            raise serializers.ValidationError("Third parties must be a list")

        return data

    def to_representation(self, instance):
        """
        Add computed fields to representation
        """
        representation = super().to_representation(instance)

        # Add validity status
        representation['is_valid'] = instance.is_valid()

        # Add days until expiry
        if instance.expiry_date:
            from django.utils import timezone
            days_until_expiry = (instance.expiry_date - timezone.now()).days
            representation['days_until_expiry'] = max(0, days_until_expiry)
        else:
            representation['days_until_expiry'] = None

        return representation


class ConsentAuditLogSerializer(serializers.ModelSerializer):
    """
    Consent audit trail serializer
    """
    action_by_name = serializers.CharField(source='action_by.get_full_name', read_only=True)
    patient_name = serializers.CharField(source='patient.get_full_name', read_only=True)
    consent_title = serializers.CharField(source='consent.title', read_only=True)

    class Meta:
        model = ConsentAuditLog
        fields = [
            'id', 'uuid', 'patient_name', 'consent_title', 'action',
            'action_by_name', 'action_date', 'details', 'ip_address',
            'user_agent', 'location', 'previous_values', 'new_values'
        ]
        read_only_fields = ['id', 'uuid', 'action_date']


class DataSubjectRequestSerializer(serializers.ModelSerializer):
    """
    GDPR data subject request serializer
    """
    patient_name = serializers.CharField(source='patient.get_full_name', read_only=True)
    patient_id = serializers.IntegerField(source='patient.id', read_only=True)
    assigned_to_name = serializers.CharField(source='assigned_to.get_full_name', read_only=True)
    completed_by_name = serializers.CharField(source='completed_by.get_full_name', read_only=True)
    days_overdue = serializers.IntegerField(read_only=True)
    processing_time_days = serializers.IntegerField(read_only=True)

    class Meta:
        model = DataSubjectRequest
        fields = [
            'id', 'uuid', 'patient_name', 'patient_id', 'request_type',
            'status', 'description', 'scope', 'timeframe', 'received_date',
            'due_date', 'completed_date', 'response_data', 'response_message',
            'rejection_reason', 'assigned_to_name', 'completed_by_name',
            'priority', 'days_overdue', 'processing_time_days',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'uuid', 'received_date', 'due_date', 'created_at', 'updated_at'
        ]

    def validate(self, data):
        """
        Validate data subject request
        """
        # Validate scope
        scope = data.get('scope', [])
        if scope and not isinstance(scope, list):
            raise serializers.ValidationError("Scope must be a list")

        # Validate timeframe
        timeframe = data.get('timeframe', {})
        if timeframe and not isinstance(timeframe, dict):
            raise serializers.ValidationError("Timeframe must be a dictionary")

        # Validate priority
        priority = data.get('priority')
        if priority and priority not in ['NORMAL', 'URGENT']:
            raise serializers.ValidationError("Priority must be 'NORMAL' or 'URGENT'")

        return data

    def to_representation(self, instance):
        """
        Add computed fields to representation
        """
        representation = super().to_representation(instance)

        # Add days overdue
        from django.utils import timezone
        if instance.due_date and instance.status != "COMPLETED":
            days_overdue = (timezone.now() - instance.due_date).days
            representation['days_overdue'] = max(0, days_overdue)
        else:
            representation['days_overdue'] = 0

        # Add processing time
        if instance.completed_date and instance.received_date:
            processing_time = (instance.completed_date - instance.received_date).days
            representation['processing_time_days'] = processing_time
        else:
            representation['processing_time_days'] = None

        return representation


class DataSubjectRequestAuditSerializer(serializers.ModelSerializer):
    """
    Data subject request audit serializer
    """
    action_by_name = serializers.CharField(source='action_by.get_full_name', read_only=True)
    request_type = serializers.CharField(source='request.request_type', read_only=True)
    patient_name = serializers.CharField(source='request.patient.get_full_name', read_only=True)

    class Meta:
        model = DataSubjectRequestAudit
        fields = [
            'id', 'uuid', 'request_type', 'patient_name', 'action',
            'action_by_name', 'action_date', 'details'
        ]
        read_only_fields = ['id', 'uuid', 'action_date']


class ConsentTypeSerializer(serializers.Serializer):
    """
    Consent type information serializer
    """
    value = serializers.CharField()
    label = serializers.CharField()
    description = serializers.CharField()


class DataSubjectRequestTypeSerializer(serializers.Serializer):
    """
    Data subject request type serializer
    """
    value = serializers.CharField()
    label = serializers.CharField()
    description = serializers.CharField()


class DataRetentionPolicySerializer(serializers.Serializer):
    """
    Data retention policy serializer
    """
    value = serializers.CharField()
    label = serializers.CharField()
    description = serializers.CharField()


class ComplianceMetricsSerializer(serializers.Serializer):
    """
    Compliance metrics serializer
    """
    total_consents = serializers.IntegerField()
    active_consents = serializers.IntegerField()
    expired_consents = serializers.IntegerField()
    revoked_consents = serializers.IntegerField()
    compliance_rate = serializers.FloatField()
    total_requests = serializers.IntegerField()
    pending_requests = serializers.IntegerField()
    completed_requests = serializers.IntegerField()
    completion_rate = serializers.FloatField()
    generated_at = serializers.DateTimeField()


class ComplianceDashboardSerializer(serializers.Serializer):
    """
    Compliance dashboard data serializer
    """
    consent_management = serializers.DictField()
    data_subject_requests = serializers.DictField()
    request_types = serializers.ListField()
    recent_activity = serializers.ListField()
    generated_at = serializers.DateTimeField()


class MFASerializer(serializers.Serializer):
    """
    Multi-Factor Authentication serializer
    """
    secret = serializers.CharField()
    provisioning_uri = serializers.CharField()
    qr_code_data = serializers.CharField(required=False)
    backup_codes = serializers.ListField(child=serializers.CharField(), required=False)


class MFATokenSerializer(serializers.Serializer):
    """
    MFA token verification serializer
    """
    token = serializers.CharField(min_length=6, max_length=6)


class MFASetupSerializer(serializers.Serializer):
    """
    MFA setup request serializer
    """
    action = serializers.ChoiceField(choices=['setup_mfa', 'verify_totp', 'verify_backup_code', 'generate_backup_codes'])
    token = serializers.CharField(required=False)
    code = serializers.CharField(required=False)


class ComplianceReportSerializer(serializers.Serializer):
    """
    Compliance report serializer
    """
    report_type = serializers.CharField()
    period = serializers.DictField()
    summary = serializers.DictField()
    details = serializers.DictField(required=False)
    generated_at = serializers.DateTimeField()
    compliance_score = serializers.FloatField(required=False)
    recommendations = serializers.ListField(child=serializers.CharField(), required=False)


class DataRetentionResultSerializer(serializers.Serializer):
    """
    Data retention execution result serializer
    """
    records_processed = serializers.IntegerField()
    records_deleted = serializers.IntegerField()
    records_anonymized = serializers.IntegerField()
    errors = serializers.ListField()


class ComplianceViolationSerializer(serializers.Serializer):
    """
    Compliance violation serializer
    """
    violation_type = serializers.CharField()
    severity = serializers.ChoiceField(choices=['LOW', 'MEDIUM', 'HIGH', 'CRITICAL'])
    description = serializers.CharField()
    affected_resources = serializers.ListField()
    detected_at = serializers.DateTimeField()
    resolved_at = serializers.DateTimeField(required=False)
    resolution_notes = serializers.CharField(required=False)


class SecurityIncidentSerializer(serializers.Serializer):
    """
    Security incident serializer
    """
    incident_type = serializers.CharField()
    severity = serializers.ChoiceField(choices=['LOW', 'MEDIUM', 'HIGH', 'CRITICAL'])
    description = serializers.CharField()
    affected_patients = serializers.ListField(required=False)
    affected_users = serializers.ListField(required=False)
    detection_method = serializers.CharField()
    reported_at = serializers.DateTimeField()
    resolved_at = serializers.DateTimeField(required=False)
    resolution_status = serializers.ChoiceField(choices=['OPEN', 'INVESTIGATING', 'RESOLVED', 'CLOSED'])
    impact_assessment = serializers.CharField(required=False)
    remediation_actions = serializers.ListField(required=False)


class BreachNotificationSerializer(serializers.Serializer):
    """
    Data breach notification serializer
    """
    breach_id = serializers.CharField()
    breach_type = serializers.CharField()
    discovery_date = serializers.DateTimeField()
    breach_date = serializers.DateTimeField()
    affected_individuals_count = serializers.IntegerField()
    phi_types_affected = serializers.ListField()
    description = serializers.CharField()
    measures_taken = serializers.CharField()
    contact_information = serializers.CharField()
    notification_status = serializers.ChoiceField(choices=['PENDING', 'SENT', 'ACKNOWLEDGED'])
    notification_date = serializers.DateTimeField(required=False)


class UserComplianceTrainingSerializer(serializers.Serializer):
    """
    User compliance training serializer
    """
    user_id = serializers.IntegerField()
    training_type = serializers.CharField()
    completion_date = serializers.DateTimeField()
    expiry_date = serializers.DateTimeField()
    certificate_url = serializers.CharField(required=False)
    status = serializers.ChoiceField(choices=['ACTIVE', 'EXPIRED', 'PENDING'])
    score = serializers.FloatField(required=False)


class AccessLogSerializer(serializers.Serializer):
    """
    PHI access log serializer
    """
    id = serializers.IntegerField()
    user_id = serializers.IntegerField()
    user_name = serializers.CharField()
    patient_id = serializers.IntegerField()
    patient_name = serializers.CharField()
    access_type = serializers.CharField()
    purpose = serializers.CharField()
    resource_type = serializers.CharField()
    resource_id = serializers.CharField()
    timestamp = serializers.DateTimeField()
    ip_address = serializers.CharField()
    user_agent = serializers.CharField()
    approved = serializers.BooleanField()


class SystemAuditLogSerializer(serializers.Serializer):
    """
    System audit log serializer
    """
    id = serializers.IntegerField()
    event_type = serializers.CharField()
    description = serializers.CharField()
    user_id = serializers.IntegerField(required=False)
    user_name = serializers.CharField(required=False)
    ip_address = serializers.CharField()
    timestamp = serializers.DateTimeField()
    metadata = serializers.DictField()


class ConsentSummarySerializer(serializers.Serializer):
    """
    Consent summary statistics serializer
    """
    total_consents = serializers.IntegerField()
    active_consents = serializers.IntegerField()
    expired_consents = serializers.IntegerField()
    revoked_consents = serializers.IntegerField()
    consents_by_type = serializers.DictField()
    consent_trends = serializers.ListField()


class DataRequestSummarySerializer(serializers.Serializer):
    """
    Data subject request summary serializer
    """
    total_requests = serializers.IntegerField()
    requests_by_type = serializers.DictField()
    requests_by_status = serializers.DictField()
    average_processing_time = serializers.FloatField()
    backlog_count = serializers.IntegerField()


class ComplianceScoreSerializer(serializers.Serializer):
    """
    Compliance score calculation serializer
    """
    overall_score = serializers.FloatField()
    consent_score = serializers.FloatField()
    data_request_score = serializers.FloatField()
    security_score = serializers.FloatField()
    privacy_score = serializers.FloatField()
    last_calculated = serializers.DateTimeField()
    score_breakdown = serializers.DictField()


class DataRetentionSummarySerializer(serializers.Serializer):
    """
    Data retention summary serializer
    """
    total_records = serializers.IntegerField()
    records_by_retention_policy = serializers.DictField()
    records_awaiting_disposal = serializers.IntegerField()
    last_retention_run = serializers.DateTimeField()
    next_retention_run = serializers.DateTimeField()


class PrivacyPolicySerializer(serializers.Serializer):
    """
    Privacy policy serializer
    """
    version = serializers.CharField()
    title = serializers.CharField()
    content = serializers.CharField()
    effective_date = serializers.DateTimeField()
    last_updated = serializers.DateTimeField()
    language = serializers.CharField()
    is_active = serializers.BooleanField()


class BusinessAssociateAgreementSerializer(serializers.Serializer):
    """
    Business Associate Agreement serializer
    """
    id = serializers.IntegerField()
    vendor_name = serializers.CharField()
    agreement_type = serializers.CharField()
    effective_date = serializers.DateTimeField()
    expiration_date = serializers.DateTimeField()
    phi_disclosure_purpose = serializers.CharField()
    safeguards_description = serializers.CharField()
    status = serializers.ChoiceField(choices=['ACTIVE', 'EXPIRED', 'TERMINATED'])
    last_review_date = serializers.DateTimeField()