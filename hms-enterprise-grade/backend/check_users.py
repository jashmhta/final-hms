#!/usr/bin/env python3

import os
import sys

import django

# Setup Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "hms.settings")
django.setup()

from django.contrib.auth import get_user_model
from django.db import transaction
from hospitals.models import Hospital

User = get_user_model()


def main():
    print("=== HMS User Check ===")

    # Check existing users
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

    # Check hospitals
    print("\nExisting hospitals:")
    hospitals = Hospital.objects.all()
    if hospitals.exists():
        for hospital in hospitals:
            print(f"- {hospital.name} ({hospital.code})")
    else:
        print("No hospitals found.")

    # Create basic users if none exist
    if not users.exists():
        print("\n=== Creating Basic Users ===")
        try:
            with transaction.atomic():
                # Create hospital first
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

                # Create superuser admin
                admin = User.objects.create_user(
                    username="admin",
                    email="admin@demo-hospital.com",
                    password="admin123",
                    first_name="Super",
                    last_name="Admin",
                    role="SUPER_ADMIN",
                    is_staff=True,
                    is_superuser=True,
                )
                print(f"Created: {admin.username} / admin123 (Super Admin)")

                # Create hospital admin
                hadmin = User.objects.create_user(
                    username="hadmin",
                    email="hadmin@demo-hospital.com",
                    password="admin123",
                    first_name="Hospital",
                    last_name="Admin",
                    role="HOSPITAL_ADMIN",
                    hospital=hospital,
                )
                print(f"Created: {hadmin.username} / admin123 (Hospital Admin)")

                # Create doctor
                doctor = User.objects.create_user(
                    username="doctor",
                    email="doctor@demo-hospital.com",
                    password="doctor123",
                    first_name="Dr. John",
                    last_name="Smith",
                    role="DOCTOR",
                    hospital=hospital,
                )
                print(f"Created: {doctor.username} / doctor123 (Doctor)")

                # Create nurse
                nurse = User.objects.create_user(
                    username="nurse",
                    email="nurse@demo-hospital.com",
                    password="nurse123",
                    first_name="Jane",
                    last_name="Doe",
                    role="NURSE",
                    hospital=hospital,
                )
                print(f"Created: {nurse.username} / nurse123 (Nurse)")

                print("\n=== Login Credentials Summary ===")
                print("Backend Django Admin (http://127.0.0.1:8000/admin/):")
                print("  - admin / admin123 (Super Admin)")
                print("  - hadmin / admin123 (Hospital Admin)")
                print("\nFrontend Application (http://localhost:5173):")
                print("  - admin / admin123 (Super Admin)")
                print("  - hadmin / admin123 (Hospital Admin)")
                print("  - doctor / doctor123 (Doctor)")
                print("  - nurse / nurse123 (Nurse)")

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
