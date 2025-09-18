import uuid
import django.core.validators
import django.db.models.deletion
import django.utils.timezone
import encrypted_model_fields.fields
from django.conf import settings
from django.db import migrations, models
class Migration(migrations.Migration):
    dependencies = [
        (
            "patients",
            "0003_emergencycontact_insuranceinformation_patientalert_and_more",
        ),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("ehr", "0002_encounterattachment"),
    ]
    operations = [
        migrations.CreateModel(
            name="Allergy",
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
                ("allergen", models.CharField(max_length=200)),
                (
                    "allergen_type",
                    models.CharField(
                        choices=[
                            ("MEDICATION", "Medication"),
                            ("FOOD", "Food"),
                            ("ENVIRONMENTAL", "Environmental"),
                            ("CONTACT", "Contact"),
                            ("OTHER", "Other"),
                        ],
                        max_length=20,
                    ),
                ),
                (
                    "reaction",
                    models.TextField(help_text="Description of allergic reaction"),
                ),
                (
                    "severity",
                    models.CharField(
                        choices=[
                            ("MILD", "Mild"),
                            ("MODERATE", "Moderate"),
                            ("SEVERE", "Severe"),
                            ("LIFE_THREAT", "Life Threatening"),
                        ],
                        max_length=15,
                    ),
                ),
                ("onset_date", models.DateField(blank=True, null=True)),
                ("verified_date", models.DateField(blank=True, null=True)),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("ACTIVE", "Active"),
                            ("INACTIVE", "Inactive"),
                            ("RESOLVED", "Resolved"),
                            ("UNCONFIRMED", "Unconfirmed"),
                        ],
                        default="ACTIVE",
                        max_length=15,
                    ),
                ),
                ("notes", models.TextField(blank=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "ordering": ["-severity", "allergen"],
            },
        ),
        migrations.CreateModel(
            name="Assessment",
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
                    "diagnosis_code",
                    models.CharField(
                        blank=True, help_text="ICD-10 code", max_length=20
                    ),
                ),
                (
                    "diagnosis_description",
                    models.CharField(default="Unknown", max_length=500),
                ),
                (
                    "diagnosis_type",
                    models.CharField(
                        choices=[
                            ("PRIMARY", "Primary Diagnosis"),
                            ("SECONDARY", "Secondary Diagnosis"),
                            ("WORKING", "Working Diagnosis"),
                            ("DIFFERENTIAL", "Differential Diagnosis"),
                            ("ADMITTING", "Admitting Diagnosis"),
                            ("DISCHARGE", "Discharge Diagnosis"),
                        ],
                        default="PRIMARY",
                        max_length=15,
                    ),
                ),
                (
                    "severity",
                    models.CharField(
                        blank=True,
                        choices=[
                            ("MILD", "Mild"),
                            ("MODERATE", "Moderate"),
                            ("SEVERE", "Severe"),
                            ("CRITICAL", "Critical"),
                        ],
                        max_length=10,
                    ),
                ),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("ACTIVE", "Active"),
                            ("RESOLVED", "Resolved"),
                            ("CHRONIC", "Chronic"),
                            ("REMISSION", "In Remission"),
                            ("RECURRENT", "Recurrent"),
                        ],
                        default="ACTIVE",
                        max_length=15,
                    ),
                ),
                ("onset_date", models.DateField(blank=True, null=True)),
                ("resolved_date", models.DateField(blank=True, null=True)),
                (
                    "confidence_level",
                    models.CharField(
                        choices=[
                            ("LOW", "Low"),
                            ("MEDIUM", "Medium"),
                            ("HIGH", "High"),
                            ("CONFIRMED", "Confirmed"),
                        ],
                        default="MEDIUM",
                        max_length=10,
                    ),
                ),
                (
                    "notes",
                    encrypted_model_fields.fields.EncryptedTextField(blank=True),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "ordering": ["-created_at"],
            },
        ),
        migrations.CreateModel(
            name="ClinicalNote",
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
                    "note_type",
                    models.CharField(
                        choices=[
                            ("PROGRESS", "Progress Note"),
                            ("SOAP", "SOAP Note"),
                            ("ADMISSION", "Admission Note"),
                            ("DISCHARGE", "Discharge Note"),
                            ("CONSULTATION", "Consultation Note"),
                            ("PROCEDURE", "Procedure Note"),
                            ("PHONE_CALL", "Phone Call Note"),
                            ("NURSING", "Nursing Note"),
                            ("THERAPY", "Therapy Note"),
                            ("EDUCATION", "Patient Education"),
                            ("OTHER", "Other"),
                        ],
                        default="PROGRESS",
                        max_length=20,
                    ),
                ),
                (
                    "subjective",
                    encrypted_model_fields.fields.EncryptedTextField(
                        blank=True, help_text="Patient's subjective complaints"
                    ),
                ),
                (
                    "objective",
                    encrypted_model_fields.fields.EncryptedTextField(
                        blank=True,
                        help_text="Objective findings and observations",
                    ),
                ),
                (
                    "assessment",
                    encrypted_model_fields.fields.EncryptedTextField(
                        blank=True,
                        help_text="Clinical assessment and diagnosis",
                    ),
                ),
                (
                    "plan",
                    encrypted_model_fields.fields.EncryptedTextField(
                        blank=True, help_text="Treatment plan and next steps"
                    ),
                ),
                (
                    "content",
                    encrypted_model_fields.fields.EncryptedTextField(
                        blank=True, help_text="Free-form note content"
                    ),
                ),
                ("is_signed", models.BooleanField(default=False)),
                ("signed_at", models.DateTimeField(blank=True, null=True)),
                ("is_amended", models.BooleanField(default=False)),
                ("amendment_reason", models.TextField(blank=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "ordering": ["-created_at"],
            },
        ),
        migrations.CreateModel(
            name="PlanOfCare",
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
                    "plan_type",
                    models.CharField(
                        choices=[
                            ("MEDICATION", "Medication"),
                            ("PROCEDURE", "Procedure"),
                            ("THERAPY", "Therapy"),
                            ("FOLLOW_UP", "Follow-up"),
                            ("LIFESTYLE", "Lifestyle Change"),
                            ("EDUCATION", "Patient Education"),
                            ("MONITORING", "Monitoring"),
                            ("REFERRAL", "Referral"),
                            ("DIAGNOSTIC", "Diagnostic Test"),
                            ("OTHER", "Other"),
                        ],
                        max_length=20,
                    ),
                ),
                ("title", models.CharField(max_length=200)),
                (
                    "description",
                    encrypted_model_fields.fields.EncryptedTextField(),
                ),
                (
                    "instructions",
                    encrypted_model_fields.fields.EncryptedTextField(blank=True),
                ),
                ("start_date", models.DateField(blank=True, null=True)),
                ("end_date", models.DateField(blank=True, null=True)),
                ("frequency", models.CharField(blank=True, max_length=100)),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("ACTIVE", "Active"),
                            ("COMPLETED", "Completed"),
                            ("CANCELLED", "Cancelled"),
                            ("ON_HOLD", "On Hold"),
                        ],
                        default="ACTIVE",
                        max_length=15,
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
                        ],
                        default="NORMAL",
                        max_length=10,
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "ordering": ["-priority", "-created_at"],
            },
        ),
        migrations.CreateModel(
            name="VitalSigns",
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
                    "systolic_bp",
                    models.PositiveIntegerField(
                        blank=True,
                        help_text="Systolic blood pressure in mmHg",
                        null=True,
                        validators=[
                            django.core.validators.MinValueValidator(50),
                            django.core.validators.MaxValueValidator(300),
                        ],
                    ),
                ),
                (
                    "diastolic_bp",
                    models.PositiveIntegerField(
                        blank=True,
                        help_text="Diastolic blood pressure in mmHg",
                        null=True,
                        validators=[
                            django.core.validators.MinValueValidator(30),
                            django.core.validators.MaxValueValidator(200),
                        ],
                    ),
                ),
                (
                    "heart_rate",
                    models.PositiveIntegerField(
                        blank=True,
                        help_text="Heart rate in beats per minute",
                        null=True,
                        validators=[
                            django.core.validators.MinValueValidator(20),
                            django.core.validators.MaxValueValidator(250),
                        ],
                    ),
                ),
                (
                    "respiratory_rate",
                    models.PositiveIntegerField(
                        blank=True,
                        help_text="Respiratory rate per minute",
                        null=True,
                        validators=[
                            django.core.validators.MinValueValidator(5),
                            django.core.validators.MaxValueValidator(100),
                        ],
                    ),
                ),
                (
                    "temperature_celsius",
                    models.DecimalField(
                        blank=True,
                        decimal_places=1,
                        help_text="Temperature in Celsius",
                        max_digits=4,
                        null=True,
                        validators=[
                            django.core.validators.MinValueValidator(30.0),
                            django.core.validators.MaxValueValidator(50.0),
                        ],
                    ),
                ),
                (
                    "oxygen_saturation",
                    models.PositiveIntegerField(
                        blank=True,
                        help_text="Oxygen saturation percentage",
                        null=True,
                        validators=[
                            django.core.validators.MinValueValidator(50),
                            django.core.validators.MaxValueValidator(100),
                        ],
                    ),
                ),
                (
                    "height_cm",
                    models.DecimalField(
                        blank=True,
                        decimal_places=2,
                        help_text="Height in centimeters",
                        max_digits=6,
                        null=True,
                        validators=[
                            django.core.validators.MinValueValidator(30.0),
                            django.core.validators.MaxValueValidator(300.0),
                        ],
                    ),
                ),
                (
                    "weight_kg",
                    models.DecimalField(
                        blank=True,
                        decimal_places=2,
                        help_text="Weight in kilograms",
                        max_digits=6,
                        null=True,
                        validators=[
                            django.core.validators.MinValueValidator(0.5),
                            django.core.validators.MaxValueValidator(1000.0),
                        ],
                    ),
                ),
                (
                    "bmi",
                    models.DecimalField(
                        blank=True,
                        decimal_places=2,
                        help_text="Body Mass Index (calculated)",
                        max_digits=5,
                        null=True,
                    ),
                ),
                (
                    "pain_score",
                    models.PositiveIntegerField(
                        blank=True,
                        help_text="Pain score (0-10 scale)",
                        null=True,
                        validators=[
                            django.core.validators.MinValueValidator(0),
                            django.core.validators.MaxValueValidator(10),
                        ],
                    ),
                ),
                (
                    "pain_location",
                    models.CharField(blank=True, max_length=200),
                ),
                (
                    "head_circumference_cm",
                    models.DecimalField(
                        blank=True,
                        decimal_places=2,
                        help_text="Head circumference in cm (for pediatrics)",
                        max_digits=5,
                        null=True,
                    ),
                ),
                (
                    "recorded_at",
                    models.DateTimeField(default=django.utils.timezone.now),
                ),
                ("device_used", models.CharField(blank=True, max_length=100)),
                ("notes", models.TextField(blank=True)),
            ],
            options={
                "ordering": ["-recorded_at"],
            },
        ),
        migrations.RemoveField(
            model_name="encounternote",
            name="author",
        ),
        migrations.RemoveField(
            model_name="encounternote",
            name="encounter",
        ),
        migrations.AlterModelOptions(
            name="encounter",
            options={"ordering": ["-scheduled_start"]},
        ),
        migrations.RemoveField(
            model_name="encounter",
            name="doctor",
        ),
        migrations.AddField(
            model_name="encounter",
            name="actual_end",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="encounter",
            name="actual_start",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="encounter",
            name="attending_physician",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="attending_encounters",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AddField(
            model_name="encounter",
            name="authorization_number",
            field=models.CharField(blank=True, max_length=100),
        ),
        migrations.AddField(
            model_name="encounter",
            name="bed",
            field=models.CharField(blank=True, max_length=50),
        ),
        migrations.AddField(
            model_name="encounter",
            name="chief_complaint",
            field=encrypted_model_fields.fields.EncryptedTextField(blank=True),
        ),
        migrations.AddField(
            model_name="encounter",
            name="consulting_physicians",
            field=models.ManyToManyField(
                blank=True,
                related_name="consulting_encounters",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AddField(
            model_name="encounter",
            name="created_by",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="created_encounters",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AddField(
            model_name="encounter",
            name="discharge_instructions",
            field=encrypted_model_fields.fields.EncryptedTextField(blank=True),
        ),
        migrations.AddField(
            model_name="encounter",
            name="disposition",
            field=models.CharField(
                blank=True,
                choices=[
                    ("DISCHARGED_HOME", "Discharged Home"),
                    ("ADMITTED", "Admitted"),
                    ("TRANSFERRED", "Transferred"),
                    ("REFERRED", "Referred"),
                    ("FOLLOW_UP", "Follow-up Required"),
                    ("OBSERVATION", "Observation"),
                    ("LEFT_AMA", "Left Against Medical Advice"),
                    ("DECEASED", "Deceased"),
                ],
                max_length=20,
            ),
        ),
        migrations.AddField(
            model_name="encounter",
            name="disposition_notes",
            field=encrypted_model_fields.fields.EncryptedTextField(blank=True),
        ),
        migrations.AddField(
            model_name="encounter",
            name="encounter_number",
            field=models.CharField(
                db_index=True, default="TEMP", max_length=50, unique=True
            ),
        ),
        migrations.AddField(
            model_name="encounter",
            name="encounter_status",
            field=models.CharField(
                choices=[
                    ("SCHEDULED", "Scheduled"),
                    ("IN_PROGRESS", "In Progress"),
                    ("COMPLETED", "Completed"),
                    ("CANCELLED", "Cancelled"),
                    ("NO_SHOW", "No Show"),
                    ("RESCHEDULED", "Rescheduled"),
                ],
                default="SCHEDULED",
                max_length=15,
            ),
        ),
        migrations.AddField(
            model_name="encounter",
            name="encounter_type",
            field=models.CharField(
                choices=[
                    ("INPATIENT", "Inpatient"),
                    ("OUTPATIENT", "Outpatient"),
                    ("EMERGENCY", "Emergency"),
                    ("URGENT_CARE", "Urgent Care"),
                    ("TELEHEALTH", "Telehealth"),
                    ("HOME_VISIT", "Home Visit"),
                    ("CONSULTATION", "Consultation"),
                    ("FOLLOW_UP", "Follow-up"),
                    ("ANNUAL_PHYSICAL", "Annual Physical"),
                    ("PREVENTIVE", "Preventive Care"),
                    ("SPECIALIST", "Specialist Visit"),
                    ("SURGICAL", "Surgical Procedure"),
                    ("DIAGNOSTIC", "Diagnostic Procedure"),
                    ("THERAPY", "Therapy Session"),
                ],
                default="OUTPATIENT",
                max_length=20,
            ),
        ),
        migrations.AddField(
            model_name="encounter",
            name="history_of_present_illness",
            field=encrypted_model_fields.fields.EncryptedTextField(blank=True),
        ),
        migrations.AddField(
            model_name="encounter",
            name="is_confidential",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="encounter",
            name="location",
            field=models.CharField(blank=True, max_length=100),
        ),
        migrations.AddField(
            model_name="encounter",
            name="primary_insurance",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="primary_encounters",
                to="patients.insuranceinformation",
            ),
        ),
        migrations.AddField(
            model_name="encounter",
            name="primary_physician",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="primary_encounters",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AddField(
            model_name="encounter",
            name="priority_level",
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
            model_name="encounter",
            name="room",
            field=models.CharField(blank=True, max_length=50),
        ),
        migrations.AddField(
            model_name="encounter",
            name="scheduled_end",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="encounter",
            name="scheduled_start",
            field=models.DateTimeField(default=django.utils.timezone.now),
        ),
        migrations.AddField(
            model_name="encounter",
            name="uuid",
            field=models.UUIDField(default=uuid.uuid4, editable=False, unique=True),
        ),
        migrations.AddField(
            model_name="encounterattachment",
            name="file_type",
            field=models.CharField(
                choices=[
                    ("IMAGE", "Image"),
                    ("DOCUMENT", "Document"),
                    ("LAB_RESULT", "Lab Result"),
                    ("XRAY", "X-Ray"),
                    ("CT_SCAN", "CT Scan"),
                    ("MRI", "MRI"),
                    ("ULTRASOUND", "Ultrasound"),
                    ("ECG", "ECG"),
                    ("OTHER", "Other"),
                ],
                default="DOCUMENT",
                max_length=20,
            ),
        ),
        migrations.AddField(
            model_name="encounterattachment",
            name="is_confidential",
            field=models.BooleanField(default=False),
        ),
        migrations.AlterField(
            model_name="encounter",
            name="diagnosis",
            field=encrypted_model_fields.fields.EncryptedTextField(blank=True),
        ),
        migrations.AlterField(
            model_name="encounter",
            name="prescription_text",
            field=encrypted_model_fields.fields.EncryptedTextField(blank=True),
        ),
        migrations.AlterField(
            model_name="encounter",
            name="treatment",
            field=encrypted_model_fields.fields.EncryptedTextField(blank=True),
        ),
        migrations.AddIndex(
            model_name="encounter",
            index=models.Index(
                fields=["patient", "-scheduled_start"],
                name="ehr_encount_patient_0897cd_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="encounter",
            index=models.Index(
                fields=["primary_physician", "-scheduled_start"],
                name="ehr_encount_primary_c510d9_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="encounter",
            index=models.Index(
                fields=["encounter_status"],
                name="ehr_encount_encount_5f083e_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="encounter",
            index=models.Index(
                fields=["encounter_type"],
                name="ehr_encount_encount_da38e4_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="encounter",
            index=models.Index(
                fields=["encounter_number"],
                name="ehr_encount_encount_08fe00_idx",
            ),
        ),
        migrations.DeleteModel(
            name="EncounterNote",
        ),
        migrations.AddField(
            model_name="vitalsigns",
            name="encounter",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="vital_signs",
                to="ehr.encounter",
            ),
        ),
        migrations.AddField(
            model_name="vitalsigns",
            name="recorded_by",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AddField(
            model_name="planofcare",
            name="encounter",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="plans",
                to="ehr.encounter",
            ),
        ),
        migrations.AddField(
            model_name="planofcare",
            name="ordered_by",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AddField(
            model_name="clinicalnote",
            name="author",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="authored_notes",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AddField(
            model_name="clinicalnote",
            name="co_signed_by",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="cosigned_notes",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AddField(
            model_name="clinicalnote",
            name="encounter",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="clinical_notes",
                to="ehr.encounter",
            ),
        ),
        migrations.AddField(
            model_name="clinicalnote",
            name="original_note",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                to="ehr.clinicalnote",
            ),
        ),
        migrations.AddField(
            model_name="assessment",
            name="diagnosed_by",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AddField(
            model_name="assessment",
            name="encounter",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="assessments",
                to="ehr.encounter",
            ),
        ),
        migrations.AddField(
            model_name="allergy",
            name="patient",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="allergies",
                to="patients.patient",
            ),
        ),
        migrations.AddField(
            model_name="allergy",
            name="reported_by",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AddField(
            model_name="allergy",
            name="verified_by",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="verified_allergies",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AddIndex(
            model_name="vitalsigns",
            index=models.Index(
                fields=["encounter", "-recorded_at"],
                name="ehr_vitalsi_encount_b80d76_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="planofcare",
            index=models.Index(
                fields=["encounter", "status"],
                name="ehr_planofc_encount_68a339_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="planofcare",
            index=models.Index(
                fields=["plan_type"], name="ehr_planofc_plan_ty_affdf6_idx"
            ),
        ),
        migrations.AddIndex(
            model_name="clinicalnote",
            index=models.Index(
                fields=["encounter", "-created_at"],
                name="ehr_clinica_encount_a3738b_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="clinicalnote",
            index=models.Index(
                fields=["author"], name="ehr_clinica_author__e1285e_idx"
            ),
        ),
        migrations.AddIndex(
            model_name="clinicalnote",
            index=models.Index(
                fields=["note_type"], name="ehr_clinica_note_ty_746a79_idx"
            ),
        ),
        migrations.AddIndex(
            model_name="assessment",
            index=models.Index(
                fields=["encounter", "diagnosis_type"],
                name="ehr_assessm_encount_b15319_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="assessment",
            index=models.Index(
                fields=["diagnosis_code"],
                name="ehr_assessm_diagnos_5b0ecd_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="allergy",
            index=models.Index(
                fields=["patient", "status"],
                name="ehr_allergy_patient_f9a71a_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="allergy",
            index=models.Index(
                fields=["allergen_type"], name="ehr_allergy_allerge_eb2d9e_idx"
            ),
        ),
        migrations.AlterUniqueTogether(
            name="allergy",
            unique_together={("patient", "allergen", "allergen_type")},
        ),
        migrations.CreateModel(
            name="EncounterNote",
            fields=[],
            options={
                "proxy": True,
                "indexes": [],
                "constraints": [],
            },
            bases=("ehr.clinicalnote",),
        ),
    ]