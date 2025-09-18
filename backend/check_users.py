import os
import sys
import secrets
import string
import django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "hms.settings")
django.setup()
from django.contrib.auth import get_user_model
from django.db import transaction
from hospitals.models import Hospital
User = get_user_model()
def generate_secure_password(length=12):
    alphabet = string.ascii_letters + string.digits + "!@
    return ''.join(secrets.choice(alphabet) for _ in range(length))
def main():
    print("=== HMS User Check ===")
    print("\nExisting users:")
    users = User.objects.all()
    if users.exists():
        for user in users:
            role = getattr(user, "role", "no role")
            print(
                f"- {user.username} ({role}) - Staff: {user.is_staff}, Superuser: {user.is_superuser}"
            )
    else:
        print("No users found.")
    print("\nExisting hospitals:")
    hospitals = Hospital.objects.all()
    if hospitals.exists():
        for hospital in hospitals:
            print(f"- {hospital.name} ({hospital.code})")
    else:
        print("No hospitals found.")
    if not users.exists():
        print("\n=== Creating Basic Users ===")
        try:
            with transaction.atomic():
                hospital, created = Hospital.objects.get_or_create(
                    code="DEMO",
                    defaults={
                        "name": "Demo Hospital",
                        "address": "123 Main St",
                        "phone": "555-0123",
                        "email": "admin@demo-hospital.com",
                    },
                )
                print(
                    f"Hospital: {hospital.name} ({'created' if created else 'exists'})"
                )
                admin_password = generate_secure_password()
                admin = User.objects.create_user(
                    username="admin",
                    email="admin@demo-hospital.com",
                    password=admin_password,
                    first_name="Super",
                    last_name="Admin",
                    role="SUPER_ADMIN",
                    is_staff=True,
                    is_superuser=True,
                )
                print(f"Created: {admin.username} / {admin_password} (Super Admin)")
                hadmin_password = generate_secure_password()
                hadmin = User.objects.create_user(
                    username="hadmin",
                    email="hadmin@demo-hospital.com",
                    password=hadmin_password,
                    first_name="Hospital",
                    last_name="Admin",
                    role="HOSPITAL_ADMIN",
                    hospital=hospital,
                )
                print(f"Created: {hadmin.username} / {hadmin_password} (Hospital Admin)")
                doctor_password = generate_secure_password()
                doctor = User.objects.create_user(
                    username="doctor",
                    email="doctor@demo-hospital.com",
                    password=doctor_password,
                    first_name="Dr. John",
                    last_name="Smith",
                    role="DOCTOR",
                    hospital=hospital,
                )
                print(f"Created: {doctor.username} / {doctor_password} (Doctor)")
                nurse_password = generate_secure_password()
                nurse = User.objects.create_user(
                    username="nurse",
                    email="nurse@demo-hospital.com",
                    password=nurse_password,
                    first_name="Jane",
                    last_name="Doe",
                    role="NURSE",
                    hospital=hospital,
                )
                print(f"Created: {nurse.username} / {nurse_password} (Nurse)")
                print("\n=== Login Credentials Summary ===")
                print("Backend Django Admin (http://127.0.0.1:8000/admin/):")
                print(f"  - admin / {admin_password} (Super Admin)")
                print(f"  - hadmin / {hadmin_password} (Hospital Admin)")
                print("\nFrontend Application (http://localhost:5173):")
                print(f"  - admin / {admin_password} (Super Admin)")
                print(f"  - hadmin / {hadmin_password} (Hospital Admin)")
                print(f"  - doctor / {doctor_password} (Doctor)")
                print(f"  - nurse / {nurse_password} (Nurse)")
        except Exception as e:
            print(f"Error creating users: {e}")
    else:
        print("\n=== Login Credentials Summary ===")
        print("Backend Django Admin (http://127.0.0.1:8000/admin/):")
        print("Use any staff user above")
        print("\nFrontend Application (http://localhost:5173):")
        print("Use any user above")
if __name__ == "__main__":
    main()