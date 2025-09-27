import uuid

import encrypted_model_fields.fields

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("hospitals", "0002_plan_hospitalplan"),
        (
            "patients",
            "0003_emergencycontact_insuranceinformation_patientalert_and_more",
        ),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("appointments", "0001_initial"),
    ]
    operations = [
        migrations.CreateModel(
            name="AppointmentHistory",
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
                    "action",
                    models.CharField(
                        choices=[
                            ("CREATED", "Created"),
                            ("UPDATED", "Updated"),
                            ("CONFIRMED", "Confirmed"),
                            ("CHECKED_IN", "Checked In"),
                            ("STARTED", "Started"),
                            ("COMPLETED", "Completed"),
                            ("CANCELLED", "Cancelled"),
                            ("RESCHEDULED", "Rescheduled"),
                            ("NO_SHOW", "No Show"),
                        ],
                        max_length=15,
                    ),
                ),
                ("field_changed", models.CharField(blank=True, max_length=50)),
                ("old_value", models.TextField(blank=True)),
                ("new_value", models.TextField(blank=True)),
                ("notes", models.TextField(blank=True)),
                ("timestamp", models.DateTimeField(auto_now_add=True)),
                ("ip_address", models.GenericIPAddressField(blank=True, null=True)),
            ],
            options={
                "ordering": ["-timestamp"],
            },
        ),
        migrations.CreateModel(
            name="AppointmentReminder",
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
                    "reminder_type",
                    models.CharField(
                        choices=[
                            ("EMAIL", "Email"),
                            ("SMS", "SMS"),
                            ("PHONE", "Phone Call"),
                            ("PORTAL", "Patient Portal"),
                            ("PUSH", "Push Notification"),
                        ],
                        max_length=15,
                    ),
                ),
                ("scheduled_for", models.DateTimeField()),
                ("sent_at", models.DateTimeField(blank=True, null=True)),
                ("subject", models.CharField(blank=True, max_length=200)),
                ("message", models.TextField(blank=True)),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("PENDING", "Pending"),
                            ("SENT", "Sent"),
                            ("FAILED", "Failed"),
                            ("CANCELLED", "Cancelled"),
                        ],
                        default="PENDING",
                        max_length=10,
                    ),
                ),
                ("delivered_at", models.DateTimeField(blank=True, null=True)),
                ("response_received", models.BooleanField(default=False)),
                (
                    "response_type",
                    models.CharField(
                        blank=True,
                        choices=[
                            ("CONFIRM", "Confirmed"),
                            ("RESCHEDULE", "Reschedule Request"),
                            ("CANCEL", "Cancellation"),
                            ("OTHER", "Other"),
                        ],
                        max_length=15,
                    ),
                ),
                ("response_notes", models.TextField(blank=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "ordering": ["-scheduled_for"],
            },
        ),
        migrations.CreateModel(
            name="AppointmentResource",
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
                ("quantity", models.PositiveIntegerField(default=1)),
                ("start_time", models.DateTimeField()),
                ("end_time", models.DateTimeField()),
                ("notes", models.TextField(blank=True)),
            ],
        ),
        migrations.CreateModel(
            name="AppointmentTemplate",
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
                ("name", models.CharField(max_length=200)),
                (
                    "appointment_type",
                    models.CharField(
                        choices=[
                            ("ROUTINE", "Routine Visit"),
                            ("FOLLOW_UP", "Follow-up"),
                            ("ANNUAL_PHYSICAL", "Annual Physical"),
                            ("CONSULTATION", "Consultation"),
                            ("PROCEDURE", "Procedure"),
                            ("EMERGENCY", "Emergency"),
                            ("URGENT", "Urgent Care"),
                            ("TELEHEALTH", "Telehealth"),
                            ("PREVENTIVE", "Preventive Care"),
                            ("SPECIALIST", "Specialist Visit"),
                            ("SURGICAL", "Surgical Consultation"),
                            ("DIAGNOSTIC", "Diagnostic"),
                            ("THERAPY", "Therapy Session"),
                            ("VACCINATION", "Vaccination"),
                            ("LAB_WORK", "Lab Work"),
                            ("IMAGING", "Imaging"),
                        ],
                        max_length=20,
                    ),
                ),
                ("duration_minutes", models.PositiveIntegerField(default=30)),
                ("description", models.TextField(blank=True)),
                ("allows_online_booking", models.BooleanField(default=True)),
                ("requires_preparation", models.BooleanField(default=False)),
                ("preparation_instructions", models.TextField(blank=True)),
                ("specialty_required", models.CharField(blank=True, max_length=100)),
                ("equipment_required", models.JSONField(blank=True, default=list)),
                ("advance_booking_days", models.PositiveIntegerField(default=1)),
                ("cancellation_hours", models.PositiveIntegerField(default=24)),
                (
                    "base_cost",
                    models.DecimalField(
                        blank=True, decimal_places=2, max_digits=10, null=True
                    ),
                ),
                ("is_active", models.BooleanField(default=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "ordering": ["name"],
            },
        ),
        migrations.CreateModel(
            name="Resource",
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
                ("name", models.CharField(max_length=200)),
                (
                    "resource_type",
                    models.CharField(
                        choices=[
                            ("ROOM", "Room"),
                            ("EQUIPMENT", "Equipment"),
                            ("BED", "Bed"),
                            ("VEHICLE", "Vehicle"),
                            ("STAFF", "Staff"),
                            ("OTHER", "Other"),
                        ],
                        max_length=20,
                    ),
                ),
                ("description", models.TextField(blank=True)),
                ("location", models.CharField(blank=True, max_length=200)),
                ("capacity", models.PositiveIntegerField(default=1)),
                ("is_bookable", models.BooleanField(default=True)),
                ("requires_approval", models.BooleanField(default=False)),
                (
                    "min_booking_duration",
                    models.PositiveIntegerField(
                        default=15, help_text="Minimum booking duration in minutes"
                    ),
                ),
                (
                    "max_booking_duration",
                    models.PositiveIntegerField(
                        default=480, help_text="Maximum booking duration in minutes"
                    ),
                ),
                (
                    "hourly_rate",
                    models.DecimalField(
                        blank=True, decimal_places=2, max_digits=10, null=True
                    ),
                ),
                ("is_active", models.BooleanField(default=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "ordering": ["name"],
            },
        ),
        migrations.CreateModel(
            name="WaitList",
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
                    "appointment_type",
                    models.CharField(
                        choices=[
                            ("ROUTINE", "Routine Visit"),
                            ("FOLLOW_UP", "Follow-up"),
                            ("ANNUAL_PHYSICAL", "Annual Physical"),
                            ("CONSULTATION", "Consultation"),
                            ("PROCEDURE", "Procedure"),
                            ("EMERGENCY", "Emergency"),
                            ("URGENT", "Urgent Care"),
                            ("TELEHEALTH", "Telehealth"),
                            ("PREVENTIVE", "Preventive Care"),
                            ("SPECIALIST", "Specialist Visit"),
                            ("SURGICAL", "Surgical Consultation"),
                            ("DIAGNOSTIC", "Diagnostic"),
                            ("THERAPY", "Therapy Session"),
                            ("VACCINATION", "Vaccination"),
                            ("LAB_WORK", "Lab Work"),
                            ("IMAGING", "Imaging"),
                        ],
                        max_length=20,
                    ),
                ),
                ("preferred_date_from", models.DateField()),
                ("preferred_date_to", models.DateField()),
                (
                    "preferred_times",
                    models.JSONField(
                        default=list, help_text="List of preferred time slots"
                    ),
                ),
                (
                    "priority",
                    models.CharField(
                        choices=[
                            ("LOW", "Low"),
                            ("NORMAL", "Normal"),
                            ("HIGH", "High"),
                            ("URGENT", "Urgent"),
                            ("EMERGENT", "Emergent"),
                        ],
                        default="NORMAL",
                        max_length=10,
                    ),
                ),
                ("reason", models.CharField(blank=True, max_length=255)),
                ("notes", models.TextField(blank=True)),
                ("is_active", models.BooleanField(default=True)),
                ("notified_count", models.PositiveIntegerField(default=0)),
                ("last_notification", models.DateTimeField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "ordering": ["priority", "created_at"],
            },
        ),
        migrations.RemoveIndex(
            model_name="appointment",
            name="appointment_hospita_333639_idx",
        ),
        migrations.RemoveField(
            model_name="appointment",
            name="doctor",
        ),
        migrations.RemoveField(
            model_name="appointment",
            name="notes",
        ),
        migrations.AddField(
            model_name="appointment",
            name="additional_providers",
            field=models.ManyToManyField(
                blank=True,
                related_name="additional_appointments",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AddField(
            model_name="appointment",
            name="appointment_number",
            field=models.CharField(
                db_index=True, default="TEMP", max_length=50, unique=True
            ),
        ),
        migrations.AddField(
            model_name="appointment",
            name="appointment_type",
            field=models.CharField(
                choices=[
                    ("ROUTINE", "Routine Visit"),
                    ("FOLLOW_UP", "Follow-up"),
                    ("ANNUAL_PHYSICAL", "Annual Physical"),
                    ("CONSULTATION", "Consultation"),
                    ("PROCEDURE", "Procedure"),
                    ("EMERGENCY", "Emergency"),
                    ("URGENT", "Urgent Care"),
                    ("TELEHEALTH", "Telehealth"),
                    ("PREVENTIVE", "Preventive Care"),
                    ("SPECIALIST", "Specialist Visit"),
                    ("SURGICAL", "Surgical Consultation"),
                    ("DIAGNOSTIC", "Diagnostic"),
                    ("THERAPY", "Therapy Session"),
                    ("VACCINATION", "Vaccination"),
                    ("LAB_WORK", "Lab Work"),
                    ("IMAGING", "Imaging"),
                ],
                default="ROUTINE",
                max_length=20,
            ),
        ),
        migrations.AddField(
            model_name="appointment",
            name="cancellation_notes",
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name="appointment",
            name="cancellation_reason",
            field=models.CharField(blank=True, max_length=200),
        ),
        migrations.AddField(
            model_name="appointment",
            name="cancelled_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="appointment",
            name="cancelled_by",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="cancelled_appointments",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AddField(
            model_name="appointment",
            name="checked_in_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="appointment",
            name="checked_in_by",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="checked_in_appointments",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AddField(
            model_name="appointment",
            name="chief_complaint",
            field=encrypted_model_fields.fields.EncryptedTextField(blank=True),
        ),
        migrations.AddField(
            model_name="appointment",
            name="clinical_notes",
            field=encrypted_model_fields.fields.EncryptedTextField(blank=True),
        ),
        migrations.AddField(
            model_name="appointment",
            name="confirmation_required",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="appointment",
            name="confirmed_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="appointment",
            name="confirmed_by",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="confirmed_appointments",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AddField(
            model_name="appointment",
            name="copay_amount",
            field=models.DecimalField(
                blank=True, decimal_places=2, max_digits=10, null=True
            ),
        ),
        migrations.AddField(
            model_name="appointment",
            name="duration_minutes",
            field=models.PositiveIntegerField(default=30),
        ),
        migrations.AddField(
            model_name="appointment",
            name="estimated_cost",
            field=models.DecimalField(
                blank=True, decimal_places=2, max_digits=10, null=True
            ),
        ),
        migrations.AddField(
            model_name="appointment",
            name="insurance_authorization",
            field=models.CharField(blank=True, max_length=100),
        ),
        migrations.AddField(
            model_name="appointment",
            name="internal_notes",
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name="appointment",
            name="interpreter_language",
            field=models.CharField(blank=True, max_length=50),
        ),
        migrations.AddField(
            model_name="appointment",
            name="is_confidential",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="appointment",
            name="is_recurring",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="appointment",
            name="is_telehealth",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="appointment",
            name="location",
            field=models.CharField(blank=True, max_length=200),
        ),
        migrations.AddField(
            model_name="appointment",
            name="no_show_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="appointment",
            name="no_show_fee",
            field=models.DecimalField(
                blank=True, decimal_places=2, max_digits=10, null=True
            ),
        ),
        migrations.AddField(
            model_name="appointment",
            name="parent_appointment",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="recurring_appointments",
                to="appointments.appointment",
            ),
        ),
        migrations.AddField(
            model_name="appointment",
            name="patient_instructions",
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name="appointment",
            name="preparation_instructions",
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name="appointment",
            name="primary_provider",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="primary_appointments",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AddField(
            model_name="appointment",
            name="priority",
            field=models.CharField(
                choices=[
                    ("LOW", "Low"),
                    ("NORMAL", "Normal"),
                    ("HIGH", "High"),
                    ("URGENT", "Urgent"),
                    ("EMERGENT", "Emergent"),
                ],
                default="NORMAL",
                max_length=10,
            ),
        ),
        migrations.AddField(
            model_name="appointment",
            name="recurrence_end_date",
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="appointment",
            name="recurrence_pattern",
            field=models.CharField(
                choices=[
                    ("NONE", "None"),
                    ("DAILY", "Daily"),
                    ("WEEKLY", "Weekly"),
                    ("BIWEEKLY", "Bi-weekly"),
                    ("MONTHLY", "Monthly"),
                    ("QUARTERLY", "Quarterly"),
                    ("ANNUALLY", "Annually"),
                    ("CUSTOM", "Custom"),
                ],
                default="NONE",
                max_length=15,
            ),
        ),
        migrations.AddField(
            model_name="appointment",
            name="reminder_sent",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="appointment",
            name="reminder_sent_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="appointment",
            name="requires_interpretation",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="appointment",
            name="requires_transportation",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="appointment",
            name="room",
            field=models.CharField(blank=True, max_length=100),
        ),
        migrations.AddField(
            model_name="appointment",
            name="scheduled_by",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="scheduled_appointments",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AddField(
            model_name="appointment",
            name="series_id",
            field=models.UUIDField(blank=True, db_index=True, null=True),
        ),
        migrations.AddField(
            model_name="appointment",
            name="special_instructions",
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name="appointment",
            name="telehealth_link",
            field=models.URLField(blank=True),
        ),
        migrations.AddField(
            model_name="appointment",
            name="telehealth_platform",
            field=models.CharField(blank=True, max_length=50),
        ),
        migrations.AddField(
            model_name="appointment",
            name="uuid",
            field=models.UUIDField(default=uuid.uuid4, editable=False, unique=True),
        ),
        migrations.AlterField(
            model_name="appointment",
            name="status",
            field=models.CharField(
                choices=[
                    ("SCHEDULED", "Scheduled"),
                    ("CONFIRMED", "Confirmed"),
                    ("CHECKED_IN", "Checked In"),
                    ("IN_PROGRESS", "In Progress"),
                    ("COMPLETED", "Completed"),
                    ("NO_SHOW", "No Show"),
                    ("CANCELLED", "Cancelled"),
                    ("RESCHEDULED", "Rescheduled"),
                    ("ON_HOLD", "On Hold"),
                ],
                default="SCHEDULED",
                max_length=16,
            ),
        ),
        migrations.AddIndex(
            model_name="appointment",
            index=models.Index(
                fields=["hospital", "primary_provider", "start_at"],
                name="appointment_hospita_d2d8df_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="appointment",
            index=models.Index(
                fields=["status", "start_at"], name="appointment_status_013fbb_idx"
            ),
        ),
        migrations.AddIndex(
            model_name="appointment",
            index=models.Index(
                fields=["appointment_type", "start_at"],
                name="appointment_appoint_75d284_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="appointment",
            index=models.Index(
                fields=["series_id"], name="appointment_series__d05f86_idx"
            ),
        ),
        migrations.AddIndex(
            model_name="appointment",
            index=models.Index(fields=["uuid"], name="appointment_uuid_1fdec5_idx"),
        ),
        migrations.AddIndex(
            model_name="appointment",
            index=models.Index(
                fields=["appointment_number"], name="appointment_appoint_93abbc_idx"
            ),
        ),
        migrations.AddField(
            model_name="waitlist",
            name="created_by",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="created_waitlist_entries",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AddField(
            model_name="waitlist",
            name="hospital",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="%(app_label)s_%(class)ss",
                to="hospitals.hospital",
            ),
        ),
        migrations.AddField(
            model_name="waitlist",
            name="patient",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="waitlist_entries",
                to="patients.patient",
            ),
        ),
        migrations.AddField(
            model_name="waitlist",
            name="provider",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="waitlist_entries",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AddField(
            model_name="resource",
            name="hospital",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="%(app_label)s_%(class)ss",
                to="hospitals.hospital",
            ),
        ),
        migrations.AddField(
            model_name="appointmenttemplate",
            name="hospital",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="%(app_label)s_%(class)ss",
                to="hospitals.hospital",
            ),
        ),
        migrations.AddField(
            model_name="appointmentresource",
            name="appointment",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                to="appointments.appointment",
            ),
        ),
        migrations.AddField(
            model_name="appointmentresource",
            name="resource",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE, to="appointments.resource"
            ),
        ),
        migrations.AddField(
            model_name="appointmentreminder",
            name="appointment",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="reminders",
                to="appointments.appointment",
            ),
        ),
        migrations.AddField(
            model_name="appointmenthistory",
            name="appointment",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="history",
                to="appointments.appointment",
            ),
        ),
        migrations.AddField(
            model_name="appointmenthistory",
            name="changed_by",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AddField(
            model_name="appointment",
            name="resources",
            field=models.ManyToManyField(
                blank=True,
                through="appointments.AppointmentResource",
                to="appointments.resource",
            ),
        ),
        migrations.AddField(
            model_name="appointment",
            name="template",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                to="appointments.appointmenttemplate",
            ),
        ),
        migrations.AddIndex(
            model_name="waitlist",
            index=models.Index(
                fields=["hospital", "provider", "is_active"],
                name="appointment_hospita_dbd3b3_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="waitlist",
            index=models.Index(
                fields=["priority", "created_at"], name="appointment_priorit_850b63_idx"
            ),
        ),
        migrations.AddIndex(
            model_name="resource",
            index=models.Index(
                fields=["hospital", "resource_type", "is_active"],
                name="appointment_hospita_ce3a94_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="appointmenttemplate",
            index=models.Index(
                fields=["hospital", "appointment_type"],
                name="appointment_hospita_45b0d3_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="appointmentresource",
            index=models.Index(
                fields=["resource", "start_time"], name="appointment_resourc_9d5d86_idx"
            ),
        ),
        migrations.AlterUniqueTogether(
            name="appointmentresource",
            unique_together={("appointment", "resource")},
        ),
        migrations.AddIndex(
            model_name="appointmentreminder",
            index=models.Index(
                fields=["appointment", "status"], name="appointment_appoint_11af41_idx"
            ),
        ),
        migrations.AddIndex(
            model_name="appointmentreminder",
            index=models.Index(
                fields=["scheduled_for", "status"],
                name="appointment_schedul_b51375_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="appointmenthistory",
            index=models.Index(
                fields=["appointment", "-timestamp"],
                name="appointment_appoint_898f2a_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="appointmenthistory",
            index=models.Index(
                fields=["action", "-timestamp"], name="appointment_action_1e6ad6_idx"
            ),
        ),
    ]
