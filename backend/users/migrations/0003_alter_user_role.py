from django.db import migrations, models
class Migration(migrations.Migration):
    dependencies = [
        ("users", "0002_department_usercredential_userloginhistory_and_more"),
    ]
    operations = [
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
                    ("DOCTOR", "Doctor"),
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
    ]