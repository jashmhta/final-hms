import encrypted_model_fields.fields

import django.core.validators
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("hospitals", "0002_plan_hospitalplan"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("ehr", "0004_alter_encounter_encounter_number"),
    ]
    operations = [
        migrations.CreateModel(
            name="ERTriage",
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
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "triage_level",
                    models.CharField(
                        choices=[
                            ("LEVEL_1", "Level 1 - Resuscitation"),
                            ("LEVEL_2", "Level 2 - Emergent"),
                            ("LEVEL_3", "Level 3 - Urgent"),
                            ("LEVEL_4", "Level 4 - Less Urgent"),
                            ("LEVEL_5", "Level 5 - Non-urgent"),
                        ],
                        default="LEVEL_3",
                        max_length=10,
                    ),
                ),
                ("chief_complaint", encrypted_model_fields.fields.EncryptedTextField()),
                ("onset_time", models.DateTimeField(blank=True, null=True)),
                (
                    "pain_scale",
                    models.PositiveIntegerField(
                        blank=True,
                        null=True,
                        validators=[
                            django.core.validators.MinValueValidator(0),
                            django.core.validators.MaxValueValidator(10),
                        ],
                    ),
                ),
                ("mechanism_of_injury", models.TextField(blank=True)),
                ("associated_symptoms", models.JSONField(blank=True, default=dict)),
                (
                    "past_medical_history_relevant",
                    encrypted_model_fields.fields.EncryptedTextField(blank=True),
                ),
                ("allergy_status", models.CharField(blank=True, max_length=20)),
                ("medication_compliance", models.BooleanField(default=False)),
                ("recent_surgeries", models.TextField(blank=True)),
                ("triage_time", models.DateTimeField(auto_now_add=True)),
                (
                    "estimated_wait_time",
                    models.PositiveIntegerField(blank=True, null=True),
                ),
                ("bed_assigned", models.CharField(blank=True, max_length=50)),
                ("reassessment_due_at", models.DateTimeField(blank=True, null=True)),
                ("last_reassessed_at", models.DateTimeField(blank=True, null=True)),
                (
                    "encounter",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="triage",
                        to="ehr.encounter",
                    ),
                ),
                (
                    "hospital",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="%(app_label)s_%(class)ss",
                        to="hospitals.hospital",
                    ),
                ),
                (
                    "initial_vitals",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        to="ehr.vitalsigns",
                    ),
                ),
                (
                    "triage_nurse",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="triage_assessments",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "ordering": ["-triage_time"],
                "indexes": [
                    models.Index(
                        fields=["encounter", "triage_level"],
                        name="ehr_ertriag_encount_3cb202_idx",
                    ),
                    models.Index(fields=["triage_time"], name="ehr_ertriag_triage__7aa9fa_idx"),
                ],
            },
        ),
    ]
