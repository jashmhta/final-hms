import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("hospitals", "0002_plan_hospitalplan"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("ehr", "0005_ertriage"),
    ]
    operations = [
        migrations.CreateModel(
            name="NotificationModel",
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
                    "notification_type",
                    models.CharField(
                        choices=[
                            ("CRITICAL_RESULT", "Critical Lab Result"),
                            ("MEDICATION_ALERT", "Medication Alert"),
                            ("APPOINTMENT_REMINDER", "Appointment Reminder"),
                            ("DISCHARGE_READY", "Discharge Ready"),
                            ("BED_AVAILABLE", "Bed Available"),
                            ("CONSULT_REQUEST", "Consultation Request"),
                        ],
                        max_length=50,
                    ),
                ),
                ("message", models.TextField()),
                (
                    "priority",
                    models.CharField(
                        choices=[
                            ("LOW", "Low"),
                            ("NORMAL", "Normal"),
                            ("HIGH", "High"),
                            ("URGENT", "Urgent"),
                        ],
                        default="NORMAL",
                        max_length=10,
                    ),
                ),
                ("is_read", models.BooleanField(default=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("read_at", models.DateTimeField(blank=True, null=True)),
            ],
            options={
                "ordering": ["-created_at"],
            },
        ),
        migrations.CreateModel(
            name="QualityMetric",
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
                    "metric_type",
                    models.CharField(
                        choices=[
                            ("PATIENT_SATISFACTION", "Patient Satisfaction"),
                            ("WAIT_TIME", "Average Wait Time"),
                            ("READMISSION_RATE", "Readmission Rate"),
                            ("INFECTION_RATE", "Infection Rate"),
                            ("MORTALITY_RATE", "Mortality Rate"),
                            ("LENGTH_OF_STAY", "Average Length of Stay"),
                        ],
                        max_length=50,
                    ),
                ),
                ("value", models.DecimalField(decimal_places=2, max_digits=10)),
                (
                    "target_value",
                    models.DecimalField(
                        blank=True, decimal_places=2, max_digits=10, null=True
                    ),
                ),
                ("period_start", models.DateField()),
                ("period_end", models.DateField()),
                ("calculated_at", models.DateTimeField(auto_now_add=True)),
            ],
            options={
                "ordering": ["-period_end"],
            },
        ),
        migrations.AddIndex(
            model_name="encounter",
            index=models.Index(
                fields=["hospital", "patient", "encounter_status"],
                name="ehr_encount_hospita_2361d5_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="encounter",
            index=models.Index(
                fields=["hospital", "primary_physician", "encounter_status"],
                name="ehr_encount_hospita_0d4cf4_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="encounter",
            index=models.Index(
                fields=["hospital", "encounter_type", "scheduled_start"],
                name="ehr_encount_hospita_29ab26_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="encounter",
            index=models.Index(
                fields=["hospital", "created_at"], name="ehr_encount_hospita_a1b086_idx"
            ),
        ),
        migrations.AddIndex(
            model_name="encounter",
            index=models.Index(
                fields=["hospital", "scheduled_start", "actual_start"],
                name="ehr_encount_hospita_d41e1f_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="encounter",
            index=models.Index(
                fields=["hospital", "priority_level"],
                name="ehr_encount_hospita_9788d7_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="encounter",
            index=models.Index(
                fields=["hospital", "is_confidential"],
                name="ehr_encount_hospita_9e5b3d_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="encounter",
            index=models.Index(
                fields=["hospital", "patient", "scheduled_start", "encounter_status"],
                name="ehr_encount_hospita_0364ac_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="encounter",
            index=models.Index(
                fields=[
                    "hospital",
                    "primary_physician",
                    "scheduled_start",
                    "encounter_status",
                ],
                name="ehr_encount_hospita_98266d_idx",
            ),
        ),
        migrations.AddField(
            model_name="qualitymetric",
            name="hospital",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="quality_metrics",
                to="hospitals.hospital",
            ),
        ),
        migrations.AddField(
            model_name="notificationmodel",
            name="encounter",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="notifications",
                to="ehr.encounter",
            ),
        ),
        migrations.AddField(
            model_name="notificationmodel",
            name="recipient_user",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="notifications",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AddIndex(
            model_name="qualitymetric",
            index=models.Index(
                fields=["hospital", "metric_type", "-period_end"],
                name="ehr_quality_hospita_57a8f0_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="notificationmodel",
            index=models.Index(
                fields=["encounter", "-created_at"],
                name="ehr_notific_encount_f244ce_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="notificationmodel",
            index=models.Index(
                fields=["recipient_user", "is_read", "-created_at"],
                name="ehr_notific_recipie_47bb40_idx",
            ),
        ),
    ]
