import uuid
from datetime import date, timedelta

from core.models import TenantModel
from django.core.validators import RegexValidator
from django.db import models
from django.utils import timezone
from encrypted_model_fields.fields import (
    EncryptedCharField,
    EncryptedEmailField,
    EncryptedTextField,
)


class PatientGender(models.TextChoices):
    MALE = "MALE", "Male"
    FEMALE = "FEMALE", "Female"
    OTHER = "OTHER", "Other"
    PREFER_NOT_TO_SAY = "PREFER_NOT_TO_SAY", "Prefer Not to Say"
    UNKNOWN = "UNKNOWN", "Unknown"


class MaritalStatus(models.TextChoices):
    SINGLE = "SINGLE", "Single"
    MARRIED = "MARRIED", "Married"
    DIVORCED = "DIVORCED", "Divorced"
    WIDOWED = "WIDOWED", "Widowed"
    SEPARATED = "SEPARATED", "Separated"
    DOMESTIC_PARTNERSHIP = "DOMESTIC_PARTNERSHIP", "Domestic Partnership"
    UNKNOWN = "UNKNOWN", "Unknown"


class BloodType(models.TextChoices):
    A_POSITIVE = "A+", "A+"
    A_NEGATIVE = "A-", "A-"
    B_POSITIVE = "B+", "B+"
    B_NEGATIVE = "B-", "B-"
    AB_POSITIVE = "AB+", "AB+"
    AB_NEGATIVE = "AB-", "AB-"
    O_POSITIVE = "O+", "O+"
    O_NEGATIVE = "O-", "O-"
    UNKNOWN = "UNKNOWN", "Unknown"


class PatientStatus(models.TextChoices):
    ACTIVE = "ACTIVE", "Active"
    INACTIVE = "INACTIVE", "Inactive"
    DECEASED = "DECEASED", "Deceased"
    TRANSFERRED = "TRANSFERRED", "Transferred"
    LOST_TO_FOLLOWUP = "LOST_TO_FOLLOWUP", "Lost to Follow-up"


class ReligionChoices(models.TextChoices):
    CHRISTIANITY = "CHRISTIANITY", "Christianity"
    ISLAM = "ISLAM", "Islam"
    JUDAISM = "JUDAISM", "Judaism"
    HINDUISM = "HINDUISM", "Hinduism"
    BUDDHISM = "BUDDHISM", "Buddhism"
    SIKHISM = "SIKHISM", "Sikhism"
    OTHER = "OTHER", "Other"
    NONE = "NONE", "None/Atheist"
    PREFER_NOT_TO_SAY = "PREFER_NOT_TO_SAY", "Prefer Not to Say"


class EthnicityChoices(models.TextChoices):
    HISPANIC_LATINO = "HISPANIC_LATINO", "Hispanic or Latino"
    NOT_HISPANIC_LATINO = "NOT_HISPANIC_LATINO", "Not Hispanic or Latino"
    UNKNOWN = "UNKNOWN", "Unknown"
    PREFER_NOT_TO_SAY = "PREFER_NOT_TO_SAY", "Prefer Not to Say"


class RaceChoices(models.TextChoices):
    AMERICAN_INDIAN = "AMERICAN_INDIAN", "American Indian or Alaska Native"
    ASIAN = "ASIAN", "Asian"
    BLACK = "BLACK", "Black or African American"
    PACIFIC_ISLANDER = "PACIFIC_ISLANDER", "Native Hawaiian or Other Pacific Islander"
    WHITE = "WHITE", "White"
    OTHER = "OTHER", "Other"
    UNKNOWN = "UNKNOWN", "Unknown"
    PREFER_NOT_TO_SAY = "PREFER_NOT_TO_SAY", "Prefer Not to Say"


class PreferredLanguage(models.TextChoices):
    ENGLISH = "EN", "English"
    SPANISH = "ES", "Spanish"
    FRENCH = "FR", "French"
    GERMAN = "DE", "German"
    ITALIAN = "IT", "Italian"
    PORTUGUESE = "PT", "Portuguese"
    RUSSIAN = "RU", "Russian"
    CHINESE = "ZH", "Chinese"
    JAPANESE = "JA", "Japanese"
    KOREAN = "KO", "Korean"
    ARABIC = "AR", "Arabic"
    HINDI = "HI", "Hindi"
    OTHER = "OTHER", "Other"


class Patient(TenantModel):
    """
    Patient model representing a healthcare patient in the HMS.

    This model stores comprehensive patient information including demographics,
    medical history, contact details, and administrative data. It supports
    multi-tenancy through the TenantModel inheritance.

    Attributes:
        uuid: Unique identifier for the patient across systems
        medical_record_number: Hospital-specific medical record number
        external_id: Identifier from external healthcare systems
        first_name: Patient's first name
        middle_name: Patient's middle name (optional)
        last_name: Patient's last name
        suffix: Name suffix (Jr., Sr., MD, etc.)
        maiden_name: Patient's maiden name (for females)
        preferred_name: Patient's preferred name for addressing
        date_of_birth: Patient's date of birth
        gender: Patient's gender identity
        marital_status: Current marital status
        race: Patient's racial background
        ethnicity: Patient's ethnic background
        religion: Patient's religious affiliation
        preferred_language: Primary language for communication
        interpreter_needed: Whether interpreter services are required
        phone_primary: Primary phone number (encrypted)
        phone_secondary: Secondary phone number (encrypted)
        email: Email address (encrypted)
        address_line1: Street address line 1 (encrypted)
        address_line2: Street address line 2 (encrypted)
        city: City of residence
        state: State/province of residence
        zip_code: Postal code
        country: Country of residence
        blood_type: ABO blood type and Rh factor
        weight_kg: Current weight in kilograms
        height_cm: Height in centimeters
        status: Current patient status (active, inactive, deceased, etc.)
        date_of_death: Date of death (if applicable)
        cause_of_death: Cause of death description
        organ_donor: Whether patient is an organ donor
        advance_directive_on_file: Whether advance directive exists
        do_not_resuscitate: DNR status
        healthcare_proxy: Healthcare proxy information
        preferred_contact_method: Preferred method of contact
        allow_sms: Whether SMS communication is allowed
        allow_email: Whether email communication is allowed
        allow_automated_calls: Whether automated calls are permitted
        hipaa_acknowledgment_date: Date HIPAA acknowledgment was signed
        privacy_notice_date: Date privacy notice was provided
        patient_portal_enrolled: Whether enrolled in patient portal
        patient_portal_last_login: Last login to patient portal
        primary_care_physician: Assigned primary care physician
        referring_physician: Referring physician
        created_by: User who created the patient record
        vip_status: Whether patient has VIP status
        confidential: Whether record is confidential
        notes: Additional notes about the patient (encrypted)
        last_updated_by: User who last updated the record

    Methods:
        get_full_name(): Returns the complete patient name
        get_age(): Calculates current age
        get_age_at_date(date): Calculates age at specific date
        is_minor(): Returns True if patient is under 18
        save(): Custom save method for MRN generation

    Meta:
        indexes: Comprehensive database indexes for performance
        ordering: Default ordering by last name, first name
    """

    # Identifiers
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    medical_record_number = models.CharField(
        max_length=50, db_index=True, default="TEMP"
    )
    external_id = models.CharField(
        max_length=100, blank=True, help_text="External system patient ID"
    )

    # Basic Information
    first_name = models.CharField(max_length=100)
    middle_name = models.CharField(max_length=100, blank=True)
    last_name = models.CharField(max_length=100)
    suffix = models.CharField(max_length=20, blank=True)
    maiden_name = models.CharField(max_length=100, blank=True)
    preferred_name = models.CharField(max_length=100, blank=True)

    # Demographics
    date_of_birth = models.DateField()
    gender = models.CharField(max_length=20, choices=PatientGender.choices)
    marital_status = models.CharField(
        max_length=25, choices=MaritalStatus.choices, default=MaritalStatus.UNKNOWN
    )

    # Diversity & Inclusion
    race = models.CharField(
        max_length=25,
        choices=RaceChoices.choices,
        default=RaceChoices.PREFER_NOT_TO_SAY,
    )
    ethnicity = models.CharField(
        max_length=25,
        choices=EthnicityChoices.choices,
        default=EthnicityChoices.PREFER_NOT_TO_SAY,
    )
    religion = models.CharField(
        max_length=25,
        choices=ReligionChoices.choices,
        default=ReligionChoices.PREFER_NOT_TO_SAY,
    )
    preferred_language = models.CharField(
        max_length=10,
        choices=PreferredLanguage.choices,
        default=PreferredLanguage.ENGLISH,
    )
    interpreter_needed = models.BooleanField(default=False)

    # Contact Information
    phone_primary = EncryptedCharField(max_length=20, blank=True)
    phone_secondary = EncryptedCharField(max_length=20, blank=True)
    email = EncryptedEmailField(blank=True)

    # Address Information
    address_line1 = EncryptedCharField(max_length=255, blank=True)
    address_line2 = EncryptedCharField(max_length=255, blank=True)
    city = models.CharField(max_length=100, blank=True)
    state = models.CharField(max_length=50, blank=True)
    zip_code = models.CharField(max_length=20, blank=True)
    country = models.CharField(max_length=50, default="US")

    # Medical Information
    blood_type = models.CharField(
        max_length=10, choices=BloodType.choices, default=BloodType.UNKNOWN
    )
    weight_kg = models.DecimalField(
        max_digits=6, decimal_places=2, null=True, blank=True
    )
    height_cm = models.DecimalField(
        max_digits=6, decimal_places=2, null=True, blank=True
    )

    # Status
    status = models.CharField(
        max_length=20, choices=PatientStatus.choices, default=PatientStatus.ACTIVE
    )
    date_of_death = models.DateField(null=True, blank=True)
    cause_of_death = models.CharField(max_length=500, blank=True)

    # Preferences & Directives
    organ_donor = models.BooleanField(default=False)
    advance_directive_on_file = models.BooleanField(default=False)
    do_not_resuscitate = models.BooleanField(default=False)
    healthcare_proxy = models.CharField(max_length=200, blank=True)

    # Communication Preferences
    preferred_contact_method = models.CharField(
        max_length=20,
        choices=[
            ("PHONE", "Phone"),
            ("EMAIL", "Email"),
            ("SMS", "Text Message"),
            ("MAIL", "Mail"),
            ("PORTAL", "Patient Portal"),
        ],
        default="PHONE",
    )
    allow_sms = models.BooleanField(default=True)
    allow_email = models.BooleanField(default=True)
    allow_automated_calls = models.BooleanField(default=False)

    # Privacy & Compliance
    hipaa_acknowledgment_date = models.DateTimeField(null=True, blank=True)
    privacy_notice_date = models.DateTimeField(null=True, blank=True)
    patient_portal_enrolled = models.BooleanField(default=False)
    patient_portal_last_login = models.DateTimeField(null=True, blank=True)

    # Clinical Information
    primary_care_physician = models.ForeignKey(
        "users.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="primary_care_patients",
    )
    referring_physician = models.ForeignKey(
        "users.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="referred_patients",
    )

    # Administrative
    created_by = models.ForeignKey(
        "users.User",
        on_delete=models.SET_NULL,
        null=True,
        related_name="created_patients",
    )
    vip_status = models.BooleanField(default=False)
    confidential = models.BooleanField(default=False)
    notes = EncryptedTextField(blank=True)

    # System Fields
    last_updated_by = models.ForeignKey(
        "users.User",
        on_delete=models.SET_NULL,
        null=True,
        related_name="updated_patients",
    )

    class Meta:
        indexes = [
            # Existing indexes
            models.Index(fields=["hospital", "last_name", "first_name"]),
            models.Index(fields=["uuid"]),
            models.Index(fields=["medical_record_number"]),
            models.Index(fields=["date_of_birth"]),
            models.Index(fields=["status"]),
            models.Index(fields=["primary_care_physician"]),
            models.Index(fields=["created_at"]),

            # Performance optimization indexes
            models.Index(fields=["hospital", "status", "created_at"]),
            models.Index(fields=["hospital", "primary_care_physician", "status"]),
            models.Index(fields=["hospital", "date_of_birth"]),
            models.Index(fields=["hospital", "gender", "status"]),
            models.Index(fields=["hospital", "city", "state"]),
            models.Index(fields=["hospital", "vip_status"]),
            models.Index(fields=["hospital", "confidential"]),
            models.Index(fields=["hospital", "patient_portal_enrolled"]),

            # Composite indexes for common queries
            models.Index(fields=["hospital", "last_name", "first_name", "status"]),
            models.Index(fields=["hospital", "medical_record_number", "status"]),
            models.Index(fields=["hospital", "primary_care_physician", "created_at"]),
        ]
        ordering = ["last_name", "first_name"]

    def __str__(self) -> str:
        return (
            f"{self.last_name}, {self.first_name} (MRN: {self.medical_record_number})"
        )

    def get_full_name(self):
        """
        Returns the complete patient name including all components.

        Returns:
            str: Full name with first, middle, last, and suffix components
        """
        parts = [self.first_name, self.middle_name, self.last_name, self.suffix]
        return " ".join(part for part in parts if part)

    def get_age(self):
        """
        Calculates the patient's current age in years.

        Returns:
            int or None: Age in years, or None if date_of_birth is not set
        """
        if not self.date_of_birth:
            return None
        today = date.today()
        return (
            today.year
            - self.date_of_birth.year
            - (
                (today.month, today.day)
                < (self.date_of_birth.month, self.date_of_birth.day)
            )
        )

    def get_age_at_date(self, reference_date):
        """
        Calculates the patient's age at a specific reference date.

        Args:
            reference_date (date): The date to calculate age at

        Returns:
            int or None: Age in years at the reference date, or None if date_of_birth is not set
        """
        if not self.date_of_birth:
            return None
        return (
            reference_date.year
            - self.date_of_birth.year
            - (
                (reference_date.month, reference_date.day)
                < (self.date_of_birth.month, self.date_of_birth.day)
            )
        )

    def is_minor(self):
        """
        Determines if the patient is a minor (under 18 years old).

        Returns:
            bool: True if patient is under 18, False otherwise
        """
        return self.get_age() < 18 if self.get_age() is not None else False

    def save(self, *args, **kwargs):
        if not self.medical_record_number:
            # Generate MRN if not provided
            import time

            timestamp = str(int(time.time()))
            self.medical_record_number = f"MRN{timestamp[-8:]}"
        super().save(*args, **kwargs)


class EmergencyContact(models.Model):
    """Emergency contact information for patients"""

    patient = models.ForeignKey(
        Patient, on_delete=models.CASCADE, related_name="emergency_contacts"
    )

    # Contact Information
    first_name = models.CharField(max_length=100)
    middle_name = models.CharField(max_length=100, blank=True)
    last_name = models.CharField(max_length=100)
    relationship = models.CharField(
        max_length=50,
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
    )

    # Contact Details
    phone_primary = EncryptedCharField(max_length=20)
    phone_secondary = EncryptedCharField(max_length=20, blank=True)
    email = EncryptedEmailField(blank=True)

    # Address
    address_line1 = EncryptedCharField(max_length=255, blank=True)
    address_line2 = EncryptedCharField(max_length=255, blank=True)
    city = models.CharField(max_length=100, blank=True)
    state = models.CharField(max_length=50, blank=True)
    zip_code = models.CharField(max_length=20, blank=True)
    country = models.CharField(max_length=50, default="US")

    # Preferences
    is_primary = models.BooleanField(default=False)
    can_make_medical_decisions = models.BooleanField(default=False)
    preferred_contact_method = models.CharField(
        max_length=20,
        choices=[
            ("PHONE", "Phone"),
            ("EMAIL", "Email"),
            ("SMS", "Text Message"),
        ],
        default="PHONE",
    )

    notes = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-is_primary", "last_name", "first_name"]
        indexes = [
            models.Index(fields=["patient", "is_primary"]),
        ]

    def __str__(self):
        return f"{self.last_name}, {self.first_name} ({self.relationship})"

    def get_full_name(self):
        parts = [self.first_name, self.middle_name, self.last_name]
        return " ".join(part for part in parts if part)


class InsuranceInformation(models.Model):
    """Patient insurance information"""

    patient = models.ForeignKey(
        Patient, on_delete=models.CASCADE, related_name="insurance_plans"
    )

    # Insurance Details
    insurance_name = models.CharField(max_length=200)
    insurance_type = models.CharField(
        max_length=20,
        choices=[
            ("PRIMARY", "Primary"),
            ("SECONDARY", "Secondary"),
            ("TERTIARY", "Tertiary"),
        ],
    )
    policy_number = EncryptedCharField(max_length=100)
    group_number = EncryptedCharField(max_length=100, blank=True)
    member_id = EncryptedCharField(max_length=100, blank=True)

    # Coverage Dates
    effective_date = models.DateField()
    termination_date = models.DateField(null=True, blank=True)

    # Insurance Company Information
    insurance_company_name = models.CharField(max_length=200)
    insurance_company_address = models.TextField(blank=True)
    insurance_company_phone = models.CharField(max_length=20, blank=True)

    # Policy Holder Information (if different from patient)
    policy_holder_name = models.CharField(max_length=200, blank=True)
    policy_holder_relationship = models.CharField(
        max_length=50,
        choices=[
            ("SELF", "Self"),
            ("SPOUSE", "Spouse"),
            ("PARENT", "Parent"),
            ("CHILD", "Child"),
            ("OTHER", "Other"),
        ],
        default="SELF",
    )
    policy_holder_dob = models.DateField(null=True, blank=True)
    policy_holder_ssn = EncryptedCharField(max_length=20, blank=True)

    # Financial Information
    copay_amount = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True
    )
    deductible_amount = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True
    )
    out_of_pocket_max = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True
    )

    # Status
    is_active = models.BooleanField(default=True)
    verification_date = models.DateField(null=True, blank=True)
    verification_status = models.CharField(
        max_length=20,
        choices=[
            ("PENDING", "Pending"),
            ("VERIFIED", "Verified"),
            ("INVALID", "Invalid"),
            ("EXPIRED", "Expired"),
        ],
        default="PENDING",
    )

    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["insurance_type", "-is_active"]
        indexes = [
            models.Index(fields=["patient", "insurance_type", "is_active"]),
            models.Index(fields=["verification_status"]),
        ]

    def __str__(self):
        return f"{self.patient} - {self.insurance_name} ({self.insurance_type})"

    def is_expired(self):
        return self.termination_date and self.termination_date < date.today()


class PatientAlert(models.Model):
    """Clinical alerts and warnings for patients"""

    patient = models.ForeignKey(
        Patient, on_delete=models.CASCADE, related_name="alerts"
    )

    alert_type = models.CharField(
        max_length=30,
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
    )

    severity = models.CharField(
        max_length=10,
        choices=[
            ("LOW", "Low"),
            ("MEDIUM", "Medium"),
            ("HIGH", "High"),
            ("CRITICAL", "Critical"),
        ],
        default="MEDIUM",
    )

    title = models.CharField(max_length=200)
    description = models.TextField()

    # Lifecycle
    is_active = models.BooleanField(default=True)
    requires_acknowledgment = models.BooleanField(default=False)
    acknowledged_by = models.ForeignKey(
        "users.User", on_delete=models.SET_NULL, null=True, blank=True
    )
    acknowledged_at = models.DateTimeField(null=True, blank=True)

    # Validity
    expires_at = models.DateTimeField(null=True, blank=True)

    created_by = models.ForeignKey(
        "users.User", on_delete=models.CASCADE, related_name="created_patient_alerts"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-severity", "-created_at"]
        indexes = [
            models.Index(fields=["patient", "is_active", "severity"]),
            models.Index(fields=["alert_type"]),
        ]

    def __str__(self):
        return f"{self.patient} - {self.title} ({self.severity})"

    def is_expired(self):
        return self.expires_at and self.expires_at < timezone.now()
