# Generated migration for compliance module

import uuid

import django.db.models.deletion
import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("patients", "0001_initial"),
        ("users", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="ConsentManagement",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "uuid",
                    models.UUIDField(default=uuid.uuid4, editable=False, unique=True),
                ),
                (
                    "consent_type",
                    models.CharField(
                        choices=[
                            ("GENERAL_TREATMENT", "General Treatment Consent"),
                            ("SPECIFIC_PROCEDURE", "Specific Procedure Consent"),
                            ("RESEARCH_PARTICIPATION", "Research Participation"),
                            ("MARKETING_COMMUNICATIONS", "Marketing Communications"),
                            ("DATA_SHARING", "Data Sharing with Third Parties"),
                            ("EMERGENCY_CONTACT", "Emergency Contact Disclosure"),
                            ("INSURANCE_BILLING", "Insurance Billing and Payment"),
                            ("TELEMEDICINE", "Telemedicine Services"),
                            ("MENTAL_HEALTH", "Mental Health Services"),
                            ("SUBSTANCE_ABUSE", "Substance Abuse Treatment"),
                            ("HIV_AIDS", "HIV/AIDS Related Information"),
                            ("GENETIC_INFORMATION", "Genetic Information"),
                        ],
                        max_length=50,
                    ),
                ),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("ACTIVE", "Active"),
                            ("EXPIRED", "Expired"),
                            ("REVOKED", "Revoked"),
                            ("PENDING", "Pending Signature"),
                            ("ARCHIVED", "Archived"),
                        ],
                        default="PENDING",
                        max_length=20,
                    ),
                ),
                ("version", models.PositiveIntegerField(default=1)),
                ("title", models.CharField(max_length=200)),
                ("description", models.TextField()),
                ("purpose", models.TextField()),
                (
                    "data_categories",
                    models.JSONField(
                        default=list, help_text="Categories of data covered by consent"
                    ),
                ),
                (
                    "third_parties",
                    models.JSONField(
                        default=list, help_text="Third parties who may receive data"
                    ),
                ),
                (
                    "retention_period",
                    models.CharField(
                        choices=[
                            ("IMMEDIATE_DELETE", "Immediate Delete"),
                            ("RETAIN_1_YEAR", "Retain 1 Year"),
                            ("RETAIN_2_YEARS", "Retain 2 Years"),
                            ("RETAIN_5_YEARS", "Retain 5 Years"),
                            ("RETAIN_7_YEARS", "Retain 7 Years"),
                            ("RETAIN_10_YEARS", "Retain 10 Years"),
                            ("RETAIN_20_YEARS", "Retain 20 Years"),
                            ("RETAIN_PERMANENT", "Retain Permanently"),
                        ],
                        max_length=30,
                    ),
                ),
                ("consent_date", models.DateTimeField(blank=True, null=True)),
                ("expiry_date", models.DateTimeField(blank=True, null=True)),
                ("revoked_date", models.DateTimeField(blank=True, null=True)),
                ("withdrawal_method", models.CharField(blank=True, max_length=50)),
                ("consent_form_url", models.URLField(blank=True)),
                ("digital_signature_data", models.JSONField(blank=True, default=dict)),
                ("witness_name", models.CharField(blank=True, max_length=100)),
                ("interpreter_used", models.BooleanField(default=False)),
                ("interpreter_name", models.CharField(blank=True, max_length=100)),
                ("language_preference", models.CharField(default="EN", max_length=10)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("is_active", models.BooleanField(default=True)),
                (
                    "hospital",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="hospitals.hospital",
                    ),
                ),
                (
                    "patient",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="consents",
                        to="patients.patient",
                    ),
                ),
                (
                    "created_by",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="created_consents",
                        to="users.user",
                    ),
                ),
            ],
            options={
                "verbose_name": "Consent Management",
                "verbose_name_plural": "Consent Management Records",
                "ordering": ["-created_at"],
                "indexes": [
                    models.Index(
                        fields=["patient", "consent_type", "status"],
                        name="comp_consent_patient_type_idx",
                    ),
                    models.Index(
                        fields=["patient", "is_active", "consent_date"],
                        name="comp_consent_patient_active_idx",
                    ),
                    models.Index(
                        fields=["expiry_date"], name="comp_consent_expiry_idx"
                    ),
                    models.Index(
                        fields=["status", "created_at"],
                        name="comp_consent_status_created_idx",
                    ),
                    models.Index(
                        fields=["hospital", "consent_type"],
                        name="comp_consent_hospital_type_idx",
                    ),
                ],
                "unique_together": {("patient", "consent_type", "version")},
            },
        ),
        migrations.CreateModel(
            name="ConsentAuditLog",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "uuid",
                    models.UUIDField(default=uuid.uuid4, editable=False, unique=True),
                ),
                (
                    "action",
                    models.CharField(help_text="Action performed", max_length=50),
                ),
                ("action_date", models.DateTimeField(auto_now_add=True)),
                ("details", models.TextField()),
                ("ip_address", models.GenericIPAddressField()),
                ("user_agent", models.TextField(blank=True)),
                ("location", models.CharField(blank=True, max_length=100)),
                ("previous_values", models.JSONField(blank=True, default=dict)),
                ("new_values", models.JSONField(blank=True, default=dict)),
                ("session_id", models.CharField(blank=True, max_length=100)),
                ("device_fingerprint", models.CharField(blank=True, max_length=100)),
                (
                    "hospital",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="hospitals.hospital",
                    ),
                ),
                (
                    "patient",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="consent_audit_logs",
                        to="patients.patient",
                    ),
                ),
                (
                    "consent",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="audit_logs",
                        to="compliance.consentmanagement",
                    ),
                ),
                (
                    "action_by",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="consent_audit_actions",
                        to="users.user",
                    ),
                ),
            ],
            options={
                "verbose_name": "Consent Audit Log",
                "verbose_name_plural": "Consent Audit Logs",
                "ordering": ["-action_date"],
                "indexes": [
                    models.Index(
                        fields=["patient", "action_date"],
                        name="comp_audit_patient_date_idx",
                    ),
                    models.Index(
                        fields=["consent", "action_date"],
                        name="comp_audit_consent_date_idx",
                    ),
                    models.Index(
                        fields=["action_by", "action_date"],
                        name="comp_audit_user_date_idx",
                    ),
                    models.Index(
                        fields=["hospital", "action_date"],
                        name="comp_audit_hospital_date_idx",
                    ),
                ],
            },
        ),
        migrations.CreateModel(
            name="DataSubjectRequest",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "uuid",
                    models.UUIDField(default=uuid.uuid4, editable=False, unique=True),
                ),
                (
                    "request_type",
                    models.CharField(
                        choices=[
                            ("ACCESS", "Right of Access"),
                            ("RECTIFICATION", "Right to Rectification"),
                            ("ERASURE", "Right to Erasure / Right to be Forgotten"),
                            ("RESTRICT", "Right to Restrict Processing"),
                            ("DATA_PORTABILITY", "Right to Data Portability"),
                            ("OBJECT", "Right to Object"),
                            (
                                "AUTOMATED_DECISION",
                                "Right Regarding Automated Decision Making",
                            ),
                        ],
                        max_length=50,
                    ),
                ),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("PENDING", "Pending Review"),
                            ("IN_PROGRESS", "In Progress"),
                            ("COMPLETED", "Completed"),
                            ("REJECTED", "Rejected"),
                            ("ESCALATED", "Escalated"),
                        ],
                        default="PENDING",
                        max_length=30,
                    ),
                ),
                ("description", models.TextField()),
                (
                    "scope",
                    models.JSONField(
                        default=list, help_text="Specific data categories requested"
                    ),
                ),
                (
                    "timeframe",
                    models.JSONField(
                        default=dict, help_text="Timeframe for data requested"
                    ),
                ),
                ("received_date", models.DateTimeField(auto_now_add=True)),
                ("due_date", models.DateTimeField()),
                ("completed_date", models.DateTimeField(blank=True, null=True)),
                ("response_data", models.JSONField(blank=True, default=dict)),
                ("response_message", models.TextField(blank=True)),
                ("rejection_reason", models.TextField(blank=True)),
                (
                    "priority",
                    models.CharField(
                        choices=[("NORMAL", "Normal"), ("URGENT", "Urgent")],
                        default="NORMAL",
                        max_length=20,
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "hospital",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="hospitals.hospital",
                    ),
                ),
                (
                    "patient",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="data_requests",
                        to="patients.patient",
                    ),
                ),
                (
                    "assigned_to",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="assigned_requests",
                        to="users.user",
                    ),
                ),
                (
                    "completed_by",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="completed_requests",
                        to="users.user",
                    ),
                ),
            ],
            options={
                "verbose_name": "Data Subject Request",
                "verbose_name_plural": "Data Subject Requests",
                "ordering": ["-received_date"],
                "indexes": [
                    models.Index(
                        fields=["patient", "request_type", "status"],
                        name="comp_ds_request_patient_type_idx",
                    ),
                    models.Index(
                        fields=["status", "due_date"],
                        name="comp_ds_request_status_due_idx",
                    ),
                    models.Index(
                        fields=["assigned_to", "status"],
                        name="comp_ds_request_assigned_status_idx",
                    ),
                    models.Index(
                        fields=["hospital", "received_date"],
                        name="comp_ds_request_hospital_date_idx",
                    ),
                ],
            },
        ),
        migrations.CreateModel(
            name="DataSubjectRequestAudit",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "uuid",
                    models.UUIDField(default=uuid.uuid4, editable=False, unique=True),
                ),
                ("action", models.CharField(max_length=50)),
                ("action_date", models.DateTimeField(auto_now_add=True)),
                ("details", models.TextField()),
                (
                    "hospital",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="hospitals.hospital",
                    ),
                ),
                (
                    "request",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="audit_logs",
                        to="compliance.datasubjectrequest",
                    ),
                ),
                (
                    "action_by",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        to="users.user",
                    ),
                ),
            ],
            options={
                "verbose_name": "Data Subject Request Audit",
                "verbose_name_plural": "Data Subject Request Audits",
                "ordering": ["-action_date"],
                "indexes": [
                    models.Index(
                        fields=["request", "action_date"],
                        name="comp_ds_audit_request_date_idx",
                    ),
                    models.Index(
                        fields=["hospital", "action_date"],
                        name="comp_ds_audit_hospital_date_idx",
                    ),
                ],
            },
        ),
    ]
