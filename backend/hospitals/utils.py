import re
import secrets
import string
from datetime import datetime, timedelta
from typing import Any, Dict, List

from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone


def generate_hospital_code(name: str) -> str:
    """
    Generate a unique hospital code based on the hospital name.

    Args:
        name: Hospital name

    Returns:
        Unique hospital code
    """
    # Remove special characters and spaces
    clean_name = re.sub(r"[^a-zA-Z0-9]", "", name)

    # Take first 3 characters and uppercase
    base_code = clean_name[:3].upper()

    # Add random suffix for uniqueness
    random_suffix = "".join(secrets.choice(string.digits) for _ in range(3))

    code = f"{base_code}{random_suffix}"

    # Check if code already exists
    from .models import Hospital

    if Hospital.objects.filter(code=code).exists():
        return generate_hospital_code(name)  # Recursive call if code exists

    return code


def validate_hospital_data(data: Dict[str, Any]) -> None:
    """
    Validate hospital data before creation/update.

    Args:
        data: Hospital data dictionary

    Raises:
        ValidationError: If data is invalid
    """
    errors = {}

    # Validate required fields
    required_fields = ["name", "address", "city", "country", "email", "phone"]
    for field in required_fields:
        if field not in data or not data[field]:
            errors[field] = f"{field.replace('_', ' ').title()} is required"

    # Validate email format
    if "email" in data and data["email"]:
        email_regex = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        if not re.match(email_regex, data["email"]):
            errors["email"] = "Invalid email format"

    # Validate phone format
    if "phone" in data and data["phone"]:
        phone_regex = r"^\+?1?\d{9,15}$"
        if not re.match(phone_regex, data["phone"].replace("-", "").replace(" ", "")):
            errors["phone"] = "Invalid phone format"

    # Validate capacity
    if "capacity" in data and data["capacity"]:
        try:
            capacity = int(data["capacity"])
            if capacity <= 0:
                errors["capacity"] = "Capacity must be a positive integer"
        except (ValueError, TypeError):
            errors["capacity"] = "Capacity must be a number"

    if errors:
        raise ValidationError(errors)


def calculate_hospital_utilization(hospital_id: int) -> Dict[str, Any]:
    """
    Calculate hospital utilization statistics.

    Args:
        hospital_id: Hospital ID

    Returns:
        Dictionary with utilization statistics
    """
    from appointments.models import Appointment
    from ehr.models import Encounter
    from patients.models import Patient

    from .models import Hospital

    try:
        hospital = Hospital.objects.get(id=hospital_id)
    except Hospital.DoesNotExist:
        return {}

    # Get current date ranges
    today = timezone.now().date()
    month_start = today.replace(day=1)

    # Calculate statistics
    total_patients = Patient.objects.filter(hospital=hospital).count()
    active_patients = Patient.objects.filter(hospital=hospital, status="ACTIVE").count()

    # Monthly statistics
    monthly_appointments = Appointment.objects.filter(
        hospital=hospital,
        appointment_date__gte=month_start,
        appointment_date__lte=today,
    ).count()

    monthly_encounters = Encounter.objects.filter(
        hospital=hospital, encounter_date__gte=month_start, encounter_date__lte=today
    ).count()

    # Calculate utilization rates
    capacity = hospital.capacity or 100
    bed_utilization = (active_patients / capacity * 100) if capacity > 0 else 0

    return {
        "hospital_id": hospital_id,
        "hospital_name": hospital.name,
        "total_patients": total_patients,
        "active_patients": active_patients,
        "monthly_appointments": monthly_appointments,
        "monthly_encounters": monthly_encounters,
        "bed_utilization_percent": round(bed_utilization, 2),
        "capacity": capacity,
        "calculated_at": timezone.now(),
    }


def get_hospital_performance_metrics(
    hospital_id: int, days: int = 30
) -> Dict[str, Any]:
    """
    Get hospital performance metrics for the specified time period.

    Args:
        hospital_id: Hospital ID
        days: Number of days to look back

    Returns:
        Dictionary with performance metrics
    """
    from appointments.models import Appointment
    from billing.models import Bill
    from patients.models import Patient

    from .models import Hospital

    try:
        hospital = Hospital.objects.get(id=hospital_id)
    except Hospital.DoesNotExist:
        return {}

    # Date range
    end_date = timezone.now()
    start_date = end_date - timedelta(days=days)

    # New patients
    new_patients = Patient.objects.filter(
        hospital=hospital, created_at__gte=start_date, created_at__lte=end_date
    ).count()

    # Appointments
    total_appointments = Appointment.objects.filter(
        hospital=hospital, created_at__gte=start_date, created_at__lte=end_date
    ).count()

    completed_appointments = Appointment.objects.filter(
        hospital=hospital,
        created_at__gte=start_date,
        created_at__lte=end_date,
        status="COMPLETED",
    ).count()

    appointment_completion_rate = (
        (completed_appointments / total_appointments * 100)
        if total_appointments > 0
        else 0
    )

    # Billing
    total_bills = Bill.objects.filter(
        hospital=hospital, created_at__gte=start_date, created_at__lte=end_date
    ).count()

    paid_bills = Bill.objects.filter(
        hospital=hospital,
        created_at__gte=start_date,
        created_at__lte=end_date,
        status="PAID",
    ).count()

    bill_payment_rate = (paid_bills / total_bills * 100) if total_bills > 0 else 0

    return {
        "hospital_id": hospital_id,
        "hospital_name": hospital.name,
        "period_days": days,
        "new_patients": new_patients,
        "total_appointments": total_appointments,
        "completed_appointments": completed_appointments,
        "appointment_completion_rate": round(appointment_completion_rate, 2),
        "total_bills": total_bills,
        "paid_bills": paid_bills,
        "bill_payment_rate": round(bill_payment_rate, 2),
        "calculated_at": timezone.now(),
    }


def validate_hospital_plan_data(data: Dict[str, Any]) -> None:
    """
    Validate hospital plan data.

    Args:
        data: Hospital plan data dictionary

    Raises:
        ValidationError: If data is invalid
    """
    errors = {}

    # Validate required fields
    required_fields = ["hospital", "plan", "start_date"]
    for field in required_fields:
        if field not in data or not data[field]:
            errors[field] = f"{field.replace('_', ' ').title()} is required"

    # Validate dates
    if "start_date" in data and data["start_date"]:
        try:
            if isinstance(data["start_date"], str):
                start_date = datetime.fromisoformat(
                    data["start_date"].replace("Z", "+00:00")
                )
            else:
                start_date = data["start_date"]

            if start_date < timezone.now():
                errors["start_date"] = "Start date cannot be in the past"
        except (ValueError, TypeError):
            errors["start_date"] = "Invalid start date format"

    if "end_date" in data and data["end_date"]:
        try:
            if isinstance(data["end_date"], str):
                end_date = datetime.fromisoformat(
                    data["end_date"].replace("Z", "+00:00")
                )
            else:
                end_date = data["end_date"]

            if "start_date" in data and data["start_date"]:
                if isinstance(data["start_date"], str):
                    start_date = datetime.fromisoformat(
                        data["start_date"].replace("Z", "+00:00")
                    )
                else:
                    start_date = data["start_date"]

                if end_date <= start_date:
                    errors["end_date"] = "End date must be after start date"
        except (ValueError, TypeError):
            errors["end_date"] = "Invalid end date format"

    if errors:
        raise ValidationError(errors)


def get_hospitals_by_plan(plan_id: int) -> List[Dict[str, Any]]:
    """
    Get all hospitals subscribed to a specific plan.

    Args:
        plan_id: Plan ID

    Returns:
        List of hospital dictionaries
    """
    from .models import HospitalPlan, Plan

    try:
        plan = Plan.objects.get(id=plan_id)
    except Plan.DoesNotExist:
        return []

    hospital_plans = HospitalPlan.objects.filter(
        plan=plan, is_active=True, end_date__gte=timezone.now().date()
    ).select_related("hospital")

    return [
        {
            "hospital_id": hp.hospital.id,
            "hospital_name": hp.hospital.name,
            "hospital_code": hp.hospital.code,
            "start_date": hp.start_date,
            "end_date": hp.end_date,
            "status": hp.hospital.status,
        }
        for hp in hospital_plans
    ]
