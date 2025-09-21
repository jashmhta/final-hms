import encrypted_model_fields.fields

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("patients", "0002_alter_patient_email_alter_patient_phone"),
    ]
    operations = [
        migrations.CreateModel(
            name="EmergencyContact",
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
                ("first_name", models.CharField(max_length=100)),
                ("middle_name", models.CharField(blank=True, max_length=100)),
                ("last_name", models.CharField(max_length=100)),
                (
                    "relationship",
                    models.CharField(
                        choices=[
                            ("SPOUSE", "Spouse"),
                            ("PARENT", "Parent"),
                            ("CHILD", "Child"),
                            ("SIBLING", "Sibling"),
                            ("GRANDPARENT", "Grandparent"),
                            ("GRANDCHILD", "Grandchild"),
                            ("FRIEND", "Friend"),
                            ("CAREGIVER", "Caregiver"),
                            ("GUARDIAN", "Legal Guardian"),
                            ("OTHER", "Other"),
                        ],
                        max_length=50,
                    ),
                ),
                ("phone_primary", encrypted_model_fields.fields.EncryptedCharField()),
                (
                    "phone_secondary",
                    encrypted_model_fields.fields.EncryptedCharField(blank=True),
                ),
                (
                    "email",
                    encrypted_model_fields.fields.EncryptedEmailField(blank=True),
                ),
                (
                    "address_line1",
                    encrypted_model_fields.fields.EncryptedCharField(blank=True),
                ),
                (
                    "address_line2",
                    encrypted_model_fields.fields.EncryptedCharField(blank=True),
                ),
                ("city", models.CharField(blank=True, max_length=100)),
                ("state", models.CharField(blank=True, max_length=50)),
                ("zip_code", models.CharField(blank=True, max_length=20)),
                ("country", models.CharField(default="US", max_length=50)),
                ("is_primary", models.BooleanField(default=False)),
                ("can_make_medical_decisions", models.BooleanField(default=False)),
                (
                    "preferred_contact_method",
                    models.CharField(
                        choices=[
                            ("PHONE", "Phone"),
                            ("EMAIL", "Email"),
                            ("SMS", "Text Message"),
                        ],
                        default="PHONE",
                        max_length=20,
                    ),
                ),
                ("notes", models.TextField(blank=True)),
                ("is_active", models.BooleanField(default=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "ordering": ["-is_primary", "last_name", "first_name"],
            },
        ),
        migrations.CreateModel(
            name="InsuranceInformation",
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
                ("insurance_name", models.CharField(max_length=200)),
                (
                    "insurance_type",
                    models.CharField(
                        choices=[
                            ("PRIMARY", "Primary"),
                            ("SECONDARY", "Secondary"),
                            ("TERTIARY", "Tertiary"),
                        ],
                        max_length=20,
                    ),
                ),
                ("policy_number", encrypted_model_fields.fields.EncryptedCharField()),
                (
                    "group_number",
                    encrypted_model_fields.fields.EncryptedCharField(blank=True),
                ),
                (
                    "member_id",
                    encrypted_model_fields.fields.EncryptedCharField(blank=True),
                ),
                ("effective_date", models.DateField()),
                ("termination_date", models.DateField(blank=True, null=True)),
                ("insurance_company_name", models.CharField(max_length=200)),
                ("insurance_company_address", models.TextField(blank=True)),
                (
                    "insurance_company_phone",
                    models.CharField(blank=True, max_length=20),
                ),
                ("policy_holder_name", models.CharField(blank=True, max_length=200)),
                (
                    "policy_holder_relationship",
                    models.CharField(
                        choices=[
                            ("SELF", "Self"),
                            ("SPOUSE", "Spouse"),
                            ("PARENT", "Parent"),
                            ("CHILD", "Child"),
                            ("OTHER", "Other"),
                        ],
                        default="SELF",
                        max_length=50,
                    ),
                ),
                ("policy_holder_dob", models.DateField(blank=True, null=True)),
                (
                    "policy_holder_ssn",
                    encrypted_model_fields.fields.EncryptedCharField(blank=True),
                ),
                (
                    "copay_amount",
                    models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True),
                ),
                (
                    "deductible_amount",
                    models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True),
                ),
                (
                    "out_of_pocket_max",
                    models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True),
                ),
                ("is_active", models.BooleanField(default=True)),
                ("verification_date", models.DateField(blank=True, null=True)),
                (
                    "verification_status",
                    models.CharField(
                        choices=[
                            ("PENDING", "Pending"),
                            ("VERIFIED", "Verified"),
                            ("INVALID", "Invalid"),
                            ("EXPIRED", "Expired"),
                        ],
                        default="PENDING",
                        max_length=20,
                    ),
                ),
                ("notes", models.TextField(blank=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "ordering": ["insurance_type", "-is_active"],
            },
        ),
        migrations.CreateModel(
            name="PatientAlert",
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
                    "alert_type",
                    models.CharField(
                        choices=[
                            ("ALLERGY", "Allergy"),
                            ("DRUG_INTERACTION", "Drug Interaction"),
                            ("FALL_RISK", "Fall Risk"),
                            ("SUICIDE_RISK", "Suicide Risk"),
                            ("INFECTION_CONTROL", "Infection Control"),
                            ("DNR", "Do Not Resuscitate"),
                            ("ADVANCE_DIRECTIVE", "Advance Directive"),
                            ("VIP", "VIP Patient"),
                            ("FINANCIAL", "Financial Alert"),
                            ("SAFETY", "Safety Alert"),
                            ("CLINICAL", "Clinical Alert"),
                            ("OTHER", "Other"),
                        ],
                        max_length=30,
                    ),
                ),
                (
                    "severity",
                    models.CharField(
                        choices=[
                            ("LOW", "Low"),
                            ("MEDIUM", "Medium"),
                            ("HIGH", "High"),
                            ("CRITICAL", "Critical"),
                        ],
                        default="MEDIUM",
                        max_length=10,
                    ),
                ),
                ("title", models.CharField(max_length=200)),
                ("description", models.TextField()),
                ("is_active", models.BooleanField(default=True)),
                ("requires_acknowledgment", models.BooleanField(default=False)),
                ("acknowledged_at", models.DateTimeField(blank=True, null=True)),
                ("expires_at", models.DateTimeField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "ordering": ["-severity", "-created_at"],
            },
        ),
        migrations.AlterUniqueTogether(
            name="patient",
            unique_together=set(),
        ),
        migrations.AddField(
            model_name="patient",
            name="address_line1",
            field=encrypted_model_fields.fields.EncryptedCharField(blank=True),
        ),
        migrations.AddField(
            model_name="patient",
            name="address_line2",
            field=encrypted_model_fields.fields.EncryptedCharField(blank=True),
        ),
        migrations.AddField(
            model_name="patient",
            name="advance_directive_on_file",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="patient",
            name="allow_automated_calls",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="patient",
            name="allow_email",
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name="patient",
            name="allow_sms",
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name="patient",
            name="blood_type",
            field=models.CharField(
                choices=[
                    ("A+", "A+"),
                    ("A-", "A-"),
                    ("B+", "B+"),
                    ("B-", "B-"),
                    ("AB+", "AB+"),
                    ("AB-", "AB-"),
                    ("O+", "O+"),
                    ("O-", "O-"),
                    ("UNKNOWN", "Unknown"),
                ],
                default="UNKNOWN",
                max_length=10,
            ),
        ),
        migrations.AddField(
            model_name="patient",
            name="cause_of_death",
            field=models.CharField(blank=True, max_length=500),
        ),
        migrations.AddField(
            model_name="patient",
            name="city",
            field=models.CharField(blank=True, max_length=100),
        ),
        migrations.AddField(
            model_name="patient",
            name="confidential",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="patient",
            name="country",
            field=models.CharField(default="US", max_length=50),
        ),
        migrations.AddField(
            model_name="patient",
            name="created_by",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="created_patients",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AddField(
            model_name="patient",
            name="date_of_death",
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="patient",
            name="do_not_resuscitate",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="patient",
            name="ethnicity",
            field=models.CharField(
                choices=[
                    ("HISPANIC_LATINO", "Hispanic or Latino"),
                    ("NOT_HISPANIC_LATINO", "Not Hispanic or Latino"),
                    ("UNKNOWN", "Unknown"),
                    ("PREFER_NOT_TO_SAY", "Prefer Not to Say"),
                ],
                default="PREFER_NOT_TO_SAY",
                max_length=25,
            ),
        ),
        migrations.AddField(
            model_name="patient",
            name="external_id",
            field=models.CharField(blank=True, help_text="External system patient ID", max_length=100),
        ),
        migrations.AddField(
            model_name="patient",
            name="healthcare_proxy",
            field=models.CharField(blank=True, max_length=200),
        ),
        migrations.AddField(
            model_name="patient",
            name="height_cm",
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=6, null=True),
        ),
        migrations.AddField(
            model_name="patient",
            name="hipaa_acknowledgment_date",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="patient",
            name="interpreter_needed",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="patient",
            name="last_updated_by",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="updated_patients",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AddField(
            model_name="patient",
            name="maiden_name",
            field=models.CharField(blank=True, max_length=100),
        ),
        migrations.AddField(
            model_name="patient",
            name="marital_status",
            field=models.CharField(
                choices=[
                    ("SINGLE", "Single"),
                    ("MARRIED", "Married"),
                    ("DIVORCED", "Divorced"),
                    ("WIDOWED", "Widowed"),
                    ("SEPARATED", "Separated"),
                    ("DOMESTIC_PARTNERSHIP", "Domestic Partnership"),
                    ("UNKNOWN", "Unknown"),
                ],
                default="UNKNOWN",
                max_length=25,
            ),
        ),
        migrations.AddField(
            model_name="patient",
            name="medical_record_number",
            field=models.CharField(db_index=True, default="TEMP", max_length=50, unique=True),
        ),
        migrations.AddField(
            model_name="patient",
            name="middle_name",
            field=models.CharField(blank=True, max_length=100),
        ),
        migrations.AddField(
            model_name="patient",
            name="notes",
            field=encrypted_model_fields.fields.EncryptedTextField(blank=True),
        ),
        migrations.AddField(
            model_name="patient",
            name="organ_donor",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="patient",
            name="patient_portal_enrolled",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="patient",
            name="patient_portal_last_login",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="patient",
            name="phone_primary",
            field=encrypted_model_fields.fields.EncryptedCharField(blank=True),
        ),
        migrations.AddField(
            model_name="patient",
            name="phone_secondary",
            field=encrypted_model_fields.fields.EncryptedCharField(blank=True),
        ),
        migrations.AddField(
            model_name="patient",
            name="preferred_contact_method",
            field=models.CharField(
                choices=[
                    ("PHONE", "Phone"),
                    ("EMAIL", "Email"),
                    ("SMS", "Text Message"),
                    ("MAIL", "Mail"),
                    ("PORTAL", "Patient Portal"),
                ],
                default="PHONE",
                max_length=20,
            ),
        ),
        migrations.AddField(
            model_name="patient",
            name="preferred_language",
            field=models.CharField(
                choices=[
                    ("EN", "English"),
                    ("ES", "Spanish"),
                    ("FR", "French"),
                    ("DE", "German"),
                    ("IT", "Italian"),
                    ("PT", "Portuguese"),
                    ("RU", "Russian"),
                    ("ZH", "Chinese"),
                    ("JA", "Japanese"),
                    ("KO", "Korean"),
                    ("AR", "Arabic"),
                    ("HI", "Hindi"),
                    ("OTHER", "Other"),
                ],
                default="EN",
                max_length=10,
            ),
        ),
        migrations.AddField(
            model_name="patient",
            name="preferred_name",
            field=models.CharField(blank=True, max_length=100),
        ),
        migrations.AddField(
            model_name="patient",
            name="primary_care_physician",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="primary_care_patients",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AddField(
            model_name="patient",
            name="privacy_notice_date",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="patient",
            name="race",
            field=models.CharField(
                choices=[
                    ("AMERICAN_INDIAN", "American Indian or Alaska Native"),
                    ("ASIAN", "Asian"),
                    ("BLACK", "Black or African American"),
                    ("PACIFIC_ISLANDER", "Native Hawaiian or Other Pacific Islander"),
                    ("WHITE", "White"),
                    ("OTHER", "Other"),
                    ("UNKNOWN", "Unknown"),
                    ("PREFER_NOT_TO_SAY", "Prefer Not to Say"),
                ],
                default="PREFER_NOT_TO_SAY",
                max_length=25,
            ),
        ),
        migrations.AddField(
            model_name="patient",
            name="referring_physician",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="referred_patients",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AddField(
            model_name="patient",
            name="religion",
            field=models.CharField(
                choices=[
                    ("CHRISTIANITY", "Christianity"),
                    ("ISLAM", "Islam"),
                    ("JUDAISM", "Judaism"),
                    ("HINDUISM", "Hinduism"),
                    ("BUDDHISM", "Buddhism"),
                    ("SIKHISM", "Sikhism"),
                    ("OTHER", "Other"),
                    ("NONE", "None/Atheist"),
                    ("PREFER_NOT_TO_SAY", "Prefer Not to Say"),
                ],
                default="PREFER_NOT_TO_SAY",
                max_length=25,
            ),
        ),
        migrations.AddField(
            model_name="patient",
            name="state",
            field=models.CharField(blank=True, max_length=50),
        ),
        migrations.AddField(
            model_name="patient",
            name="status",
            field=models.CharField(
                choices=[
                    ("ACTIVE", "Active"),
                    ("INACTIVE", "Inactive"),
                    ("DECEASED", "Deceased"),
                    ("TRANSFERRED", "Transferred"),
                    ("LOST_TO_FOLLOWUP", "Lost to Follow-up"),
                ],
                default="ACTIVE",
                max_length=20,
            ),
        ),
        migrations.AddField(
            model_name="patient",
            name="suffix",
            field=models.CharField(blank=True, max_length=20),
        ),
        migrations.AddField(
            model_name="patient",
            name="vip_status",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="patient",
            name="weight_kg",
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=6, null=True),
        ),
        migrations.AddField(
            model_name="patient",
            name="zip_code",
            field=models.CharField(blank=True, max_length=20),
        ),
        migrations.AlterField(
            model_name="patient",
            name="date_of_birth",
            field=models.DateField(),
        ),
        migrations.AlterField(
            model_name="patient",
            name="gender",
            field=models.CharField(
                choices=[
                    ("MALE", "Male"),
                    ("FEMALE", "Female"),
                    ("OTHER", "Other"),
                    ("PREFER_NOT_TO_SAY", "Prefer Not to Say"),
                    ("UNKNOWN", "Unknown"),
                ],
                max_length=20,
            ),
        ),
        migrations.AddIndex(
            model_name="patient",
            index=models.Index(fields=["medical_record_number"], name="patients_pa_medical_ff50e5_idx"),
        ),
        migrations.AddIndex(
            model_name="patient",
            index=models.Index(fields=["date_of_birth"], name="patients_pa_date_of_4302f5_idx"),
        ),
        migrations.AddIndex(
            model_name="patient",
            index=models.Index(fields=["status"], name="patients_pa_status_ca3fc5_idx"),
        ),
        migrations.AddIndex(
            model_name="patient",
            index=models.Index(fields=["primary_care_physician"], name="patients_pa_primary_b5fbf1_idx"),
        ),
        migrations.AddIndex(
            model_name="patient",
            index=models.Index(fields=["created_at"], name="patients_pa_created_542792_idx"),
        ),
        migrations.AddField(
            model_name="patientalert",
            name="acknowledged_by",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AddField(
            model_name="patientalert",
            name="created_by",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="created_patient_alerts",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AddField(
            model_name="patientalert",
            name="patient",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="alerts",
                to="patients.patient",
            ),
        ),
        migrations.AddField(
            model_name="insuranceinformation",
            name="patient",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="insurance_plans",
                to="patients.patient",
            ),
        ),
        migrations.AddField(
            model_name="emergencycontact",
            name="patient",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="emergency_contacts",
                to="patients.patient",
            ),
        ),
        migrations.RemoveField(
            model_name="patient",
            name="active",
        ),
        migrations.RemoveField(
            model_name="patient",
            name="address",
        ),
        migrations.RemoveField(
            model_name="patient",
            name="insurance_number",
        ),
        migrations.RemoveField(
            model_name="patient",
            name="insurance_provider",
        ),
        migrations.RemoveField(
            model_name="patient",
            name="phone",
        ),
        migrations.AddIndex(
            model_name="patientalert",
            index=models.Index(
                fields=["patient", "is_active", "severity"],
                name="patients_pa_patient_cb5cc3_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="patientalert",
            index=models.Index(fields=["alert_type"], name="patients_pa_alert_t_fb1d65_idx"),
        ),
        migrations.AddIndex(
            model_name="insuranceinformation",
            index=models.Index(
                fields=["patient", "insurance_type", "is_active"],
                name="patients_in_patient_e92eb1_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="insuranceinformation",
            index=models.Index(fields=["verification_status"], name="patients_in_verific_84856d_idx"),
        ),
        migrations.AddIndex(
            model_name="emergencycontact",
            index=models.Index(fields=["patient", "is_primary"], name="patients_em_patient_c7b8c7_idx"),
        ),
    ]
