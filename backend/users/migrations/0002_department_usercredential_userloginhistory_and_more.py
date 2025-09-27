import encrypted_model_fields.fields

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("auth", "0012_alter_user_first_name_max_length"),
        ("hospitals", "0002_plan_hospitalplan"),
        ("users", "0001_initial"),
    ]
    operations = [
        migrations.CreateModel(
            name="Department",
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
                ("name", models.CharField(max_length=100)),
                ("code", models.CharField(max_length=20, unique=True)),
                ("description", models.TextField(blank=True)),
                ("is_active", models.BooleanField(default=True)),
                (
                    "budget",
                    models.DecimalField(
                        blank=True, decimal_places=2, max_digits=15, null=True
                    ),
                ),
                ("location", models.CharField(blank=True, max_length=255)),
                ("phone", models.CharField(blank=True, max_length=20)),
                ("email", models.EmailField(blank=True, max_length=254)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "ordering": ["name"],
            },
        ),
        migrations.CreateModel(
            name="UserCredential",
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
                ("credential_type", models.CharField(max_length=100)),
                ("credential_name", models.CharField(max_length=200)),
                ("issuing_organization", models.CharField(max_length=200)),
                (
                    "credential_number",
                    encrypted_model_fields.fields.EncryptedCharField(
                        max_length=100, blank=True
                    ),
                ),
                ("issue_date", models.DateField()),
                ("expiry_date", models.DateField(blank=True, null=True)),
                ("is_active", models.BooleanField(default=True)),
                (
                    "verification_status",
                    models.CharField(
                        choices=[
                            ("PENDING", "Pending"),
                            ("VERIFIED", "Verified"),
                            ("EXPIRED", "Expired"),
                            ("REVOKED", "Revoked"),
                        ],
                        default="PENDING",
                        max_length=20,
                    ),
                ),
                (
                    "document",
                    models.FileField(blank=True, null=True, upload_to="credentials/"),
                ),
                ("notes", models.TextField(blank=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "ordering": ["-issue_date"],
            },
        ),
        migrations.CreateModel(
            name="UserLoginHistory",
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
                ("username_attempted", models.CharField(max_length=150)),
                ("ip_address", models.GenericIPAddressField()),
                ("user_agent", models.TextField()),
                ("success", models.BooleanField()),
                (
                    "failure_reason",
                    models.CharField(blank=True, max_length=100),
                ),
                ("timestamp", models.DateTimeField(auto_now_add=True)),
                ("location", models.CharField(blank=True, max_length=255)),
            ],
            options={
                "ordering": ["-timestamp"],
            },
        ),
        migrations.CreateModel(
            name="UserPermissionGroup",
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
                ("name", models.CharField(max_length=100)),
                ("description", models.TextField(blank=True)),
                ("is_active", models.BooleanField(default=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "ordering": ["name"],
            },
        ),
        migrations.CreateModel(
            name="UserSession",
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
                ("session_key", models.CharField(max_length=40, unique=True)),
                ("ip_address", models.GenericIPAddressField()),
                ("user_agent", models.TextField()),
                ("location", models.CharField(blank=True, max_length=255)),
                ("is_active", models.BooleanField(default=True)),
                ("login_time", models.DateTimeField(auto_now_add=True)),
                ("logout_time", models.DateTimeField(blank=True, null=True)),
                ("last_activity", models.DateTimeField(auto_now=True)),
            ],
            options={
                "ordering": ["-login_time"],
            },
        ),
        migrations.AlterModelOptions(
            name="user",
            options={
                "permissions": [
                    ("can_manage_users", "Can manage users"),
                    ("can_view_all_patients", "Can view all patients"),
                    ("can_manage_departments", "Can manage departments"),
                    ("can_access_reports", "Can access reports"),
                    ("can_manage_billing", "Can manage billing"),
                    ("can_prescribe_medication", "Can prescribe medication"),
                    ("can_order_labs", "Can order lab tests"),
                    ("can_discharge_patients", "Can discharge patients"),
                    ("can_access_admin_panel", "Can access admin panel"),
                ]
            },
        ),
        migrations.AddField(
            model_name="user",
            name="account_locked_until",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="user",
            name="address_line1",
            field=encrypted_model_fields.fields.EncryptedCharField(
                max_length=255, blank=True
            ),
        ),
        migrations.AddField(
            model_name="user",
            name="address_line2",
            field=encrypted_model_fields.fields.EncryptedCharField(
                max_length=255, blank=True
            ),
        ),
        migrations.AddField(
            model_name="user",
            name="avatar",
            field=models.ImageField(blank=True, null=True, upload_to="avatars/"),
        ),
        migrations.AddField(
            model_name="user",
            name="background_check_date",
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="user",
            name="bio",
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name="user",
            name="board_certification",
            field=models.CharField(blank=True, max_length=200),
        ),
        migrations.AddField(
            model_name="user",
            name="city",
            field=models.CharField(blank=True, max_length=100),
        ),
        migrations.AddField(
            model_name="user",
            name="country",
            field=models.CharField(default="US", max_length=50),
        ),
        migrations.AddField(
            model_name="user",
            name="created_by",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="created_users",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AddField(
            model_name="user",
            name="date_of_birth",
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="user",
            name="drug_test_date",
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="user",
            name="employee_id",
            field=models.CharField(blank=True, max_length=20, null=True, unique=True),
        ),
        migrations.AddField(
            model_name="user",
            name="employment_type",
            field=models.CharField(
                choices=[
                    ("FULL_TIME", "Full Time"),
                    ("PART_TIME", "Part Time"),
                    ("CONTRACT", "Contract"),
                    ("TEMPORARY", "Temporary"),
                    ("CONSULTANT", "Consultant"),
                    ("VOLUNTEER", "Volunteer"),
                ],
                default="FULL_TIME",
                max_length=20,
            ),
        ),
        migrations.AddField(
            model_name="user",
            name="failed_login_attempts",
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.AddField(
            model_name="user",
            name="gender",
            field=models.CharField(
                blank=True,
                choices=[("M", "Male"), ("F", "Female"), ("O", "Other")],
                max_length=10,
            ),
        ),
        migrations.AddField(
            model_name="user",
            name="hipaa_training_date",
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="user",
            name="hire_date",
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="user",
            name="hourly_rate",
            field=encrypted_model_fields.fields.EncryptedCharField(blank=True),
        ),
        migrations.AddField(
            model_name="user",
            name="last_activity",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="user",
            name="license_expiry",
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="user",
            name="license_number",
            field=encrypted_model_fields.fields.EncryptedCharField(blank=True),
        ),
        migrations.AddField(
            model_name="user",
            name="mfa_enabled",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="user",
            name="mfa_secret",
            field=encrypted_model_fields.fields.EncryptedCharField(blank=True),
        ),
        migrations.AddField(
            model_name="user",
            name="middle_name",
            field=models.CharField(blank=True, max_length=30),
        ),
        migrations.AddField(
            model_name="user",
            name="must_change_password",
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name="user",
            name="orientation_completed",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="user",
            name="password_changed_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="user",
            name="personal_email",
            field=encrypted_model_fields.fields.EncryptedEmailField(blank=True),
        ),
        migrations.AddField(
            model_name="user",
            name="personal_phone",
            field=encrypted_model_fields.fields.EncryptedCharField(blank=True),
        ),
        migrations.AddField(
            model_name="user",
            name="preferences",
            field=models.JSONField(blank=True, default=dict),
        ),
        migrations.AddField(
            model_name="user",
            name="salary",
            field=encrypted_model_fields.fields.EncryptedCharField(blank=True),
        ),
        migrations.AddField(
            model_name="user",
            name="specialization",
            field=models.CharField(blank=True, max_length=100),
        ),
        migrations.AddField(
            model_name="user",
            name="state",
            field=models.CharField(blank=True, max_length=50),
        ),
        migrations.AddField(
            model_name="user",
            name="status",
            field=models.CharField(
                choices=[
                    ("ACTIVE", "Active"),
                    ("INACTIVE", "Inactive"),
                    ("SUSPENDED", "Suspended"),
                    ("TERMINATED", "Terminated"),
                    ("ON_LEAVE", "On Leave"),
                    ("PENDING_VERIFICATION", "Pending Verification"),
                ],
                default="PENDING_VERIFICATION",
                max_length=20,
            ),
        ),
        migrations.AddField(
            model_name="user",
            name="suffix",
            field=models.CharField(blank=True, max_length=10),
        ),
        migrations.AddField(
            model_name="user",
            name="supervisor",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="supervised_users",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AddField(
            model_name="user",
            name="termination_date",
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="user",
            name="work_phone",
            field=models.CharField(blank=True, max_length=20),
        ),
        migrations.AddField(
            model_name="user",
            name="years_experience",
            field=models.PositiveIntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="user",
            name="zip_code",
            field=models.CharField(blank=True, max_length=10),
        ),
        migrations.AlterField(
            model_name="user",
            name="role",
            field=models.CharField(
                choices=[
                    ("SUPER_ADMIN", "Super Admin"),
                    ("HOSPITAL_ADMIN", "Hospital Admin"),
                    ("CHIEF_MEDICAL_OFFICER", "Chief Medical Officer"),
                    ("DEPARTMENT_HEAD", "Department Head"),
                    ("ATTENDING_PHYSICIAN", "Attending Physician"),
                    ("RESIDENT", "Resident"),
                    ("INTERN", "Intern"),
                    ("NURSE_MANAGER", "Nurse Manager"),
                    ("CHARGE_NURSE", "Charge Nurse"),
                    ("REGISTERED_NURSE", "Registered Nurse"),
                    ("LICENSED_NURSE", "Licensed Practical Nurse"),
                    ("PHARMACIST", "Pharmacist"),
                    ("PHARMACY_TECH", "Pharmacy Technician"),
                    ("LAB_DIRECTOR", "Lab Director"),
                    ("LAB_SUPERVISOR", "Lab Supervisor"),
                    ("LAB_TECH", "Lab Technician"),
                    ("RADIOLOGY_TECH", "Radiology Technician"),
                    ("RESPIRATORY_THERAPIST", "Respiratory Therapist"),
                    ("PHYSICAL_THERAPIST", "Physical Therapist"),
                    ("SOCIAL_WORKER", "Social Worker"),
                    ("CASE_MANAGER", "Case Manager"),
                    ("BILLING_MANAGER", "Billing Manager"),
                    ("BILLING_CLERK", "Billing Clerk"),
                    ("FINANCE_MANAGER", "Finance Manager"),
                    ("RECEPTIONIST", "Receptionist"),
                    ("SCHEDULER", "Scheduler"),
                    ("MEDICAL_RECORDS", "Medical Records"),
                    ("IT_ADMIN", "IT Administrator"),
                    ("SECURITY", "Security"),
                    ("MAINTENANCE", "Maintenance"),
                    ("VOLUNTEER", "Volunteer"),
                ],
                default="RECEPTIONIST",
                max_length=32,
            ),
        ),
        migrations.AddIndex(
            model_name="user",
            index=models.Index(
                fields=["role", "status"], name="users_user_role_6e67fb_idx"
            ),
        ),
        migrations.AddIndex(
            model_name="user",
            index=models.Index(
                fields=["employee_id"], name="users_user_employe_e638d5_idx"
            ),
        ),
        migrations.AddIndex(
            model_name="user",
            index=models.Index(
                fields=["last_activity"], name="users_user_last_ac_1898c4_idx"
            ),
        ),
        migrations.AddField(
            model_name="usersession",
            name="user",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="sessions",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AddField(
            model_name="userpermissiongroup",
            name="hospital",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="permission_groups",
                to="hospitals.hospital",
            ),
        ),
        migrations.AddField(
            model_name="userpermissiongroup",
            name="permissions",
            field=models.ManyToManyField(blank=True, to="auth.permission"),
        ),
        migrations.AddField(
            model_name="userpermissiongroup",
            name="users",
            field=models.ManyToManyField(
                blank=True,
                related_name="custom_permission_groups",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AddField(
            model_name="userloginhistory",
            name="user",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="login_history",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AddField(
            model_name="usercredential",
            name="user",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="credentials",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AddField(
            model_name="department",
            name="head",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="headed_departments",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AddField(
            model_name="department",
            name="hospital",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="departments",
                to="hospitals.hospital",
            ),
        ),
        migrations.AddField(
            model_name="department",
            name="parent",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="subdepartments",
                to="users.department",
            ),
        ),
        migrations.AddField(
            model_name="user",
            name="department",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="users",
                to="users.department",
            ),
        ),
        migrations.AddIndex(
            model_name="usersession",
            index=models.Index(
                fields=["user", "is_active"],
                name="users_users_user_id_3887fe_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="usersession",
            index=models.Index(
                fields=["session_key"], name="users_users_session_70af4d_idx"
            ),
        ),
        migrations.AlterUniqueTogether(
            name="userpermissiongroup",
            unique_together={("hospital", "name")},
        ),
        migrations.AddIndex(
            model_name="userloginhistory",
            index=models.Index(
                fields=["user", "timestamp"],
                name="users_userl_user_id_f72497_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="userloginhistory",
            index=models.Index(
                fields=["ip_address", "timestamp"],
                name="users_userl_ip_addr_1af4bd_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="userloginhistory",
            index=models.Index(
                fields=["success", "timestamp"],
                name="users_userl_success_bfc528_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="usercredential",
            index=models.Index(
                fields=["user", "is_active"],
                name="users_userc_user_id_1e0d9e_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="usercredential",
            index=models.Index(
                fields=["expiry_date"], name="users_userc_expiry__e79935_idx"
            ),
        ),
        migrations.AlterUniqueTogether(
            name="department",
            unique_together={("hospital", "code")},
        ),
        migrations.AddIndex(
            model_name="user",
            index=models.Index(
                fields=["hospital", "department", "status"],
                name="users_user_hospita_08b161_idx",
            ),
        ),
    ]
