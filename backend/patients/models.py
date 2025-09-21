import uuid
from datetime import date, timedelta

from encrypted_model_fields.fields import (
    EncryptedCharField,
    EncryptedEmailField,
    EncryptedTextField,
)

from django.core.cache import cache
from django.core.validators import RegexValidator
from django.db import models
from django.utils import timezone

from core.enhanced_cache import enhanced_cache
from core.models import TenantModel
from core.optimization.query_optimizer import QueryOptimizer, profile_queries


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
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    medical_record_number = models.CharField(max_length=50, db_index=True, default="TEMP")
    external_id = models.CharField(max_length=100, blank=True, help_text="External system patient ID")
    first_name = EncryptedCharField(max_length=100)
    middle_name = EncryptedCharField(max_length=100, blank=True)
    last_name = EncryptedCharField(max_length=100)
    suffix = EncryptedCharField(max_length=20, blank=True)
    maiden_name = EncryptedCharField(max_length=100, blank=True)
    preferred_name = EncryptedCharField(max_length=100, blank=True)
    date_of_birth = models.DateField()
    gender = models.CharField(max_length=20, choices=PatientGender.choices)
    marital_status = models.CharField(max_length=25, choices=MaritalStatus.choices, default=MaritalStatus.UNKNOWN)
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
    phone_primary = EncryptedCharField(max_length=20, blank=True)
    phone_secondary = EncryptedCharField(max_length=20, blank=True)
    email = EncryptedEmailField(blank=True)
    address_line1 = EncryptedCharField(max_length=255, blank=True)
    address_line2 = EncryptedCharField(max_length=255, blank=True)
    city = models.CharField(max_length=100, blank=True)
    state = models.CharField(max_length=50, blank=True)
    zip_code = models.CharField(max_length=20, blank=True)
    country = models.CharField(max_length=50, default="US")
    blood_type = models.CharField(max_length=10, choices=BloodType.choices, default=BloodType.UNKNOWN)
    weight_kg = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    height_cm = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    status = models.CharField(max_length=20, choices=PatientStatus.choices, default=PatientStatus.ACTIVE)
    date_of_death = models.DateField(null=True, blank=True)
    cause_of_death = models.CharField(max_length=500, blank=True)
    organ_donor = models.BooleanField(default=False)
    advance_directive_on_file = models.BooleanField(default=False)
    do_not_resuscitate = models.BooleanField(default=False)
    healthcare_proxy = models.CharField(max_length=200, blank=True)
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
    hipaa_acknowledgment_date = models.DateTimeField(null=True, blank=True)
    privacy_notice_date = models.DateTimeField(null=True, blank=True)
    patient_portal_enrolled = models.BooleanField(default=False)
    patient_portal_last_login = models.DateTimeField(null=True, blank=True)
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
    created_by = models.ForeignKey(
        "users.User",
        on_delete=models.SET_NULL,
        null=True,
        related_name="created_patients",
    )
    vip_status = models.BooleanField(default=False)
    confidential = models.BooleanField(default=False)
    notes = EncryptedTextField(blank=True)
    last_updated_by = models.ForeignKey(
        "users.User",
        on_delete=models.SET_NULL,
        null=True,
        related_name="updated_patients",
    )

    class Meta:
        indexes = [
            models.Index(fields=["hospital", "last_name", "first_name"]),
            models.Index(fields=["uuid"]),
            models.Index(fields=["medical_record_number"]),
            models.Index(fields=["date_of_birth"]),
            models.Index(fields=["status"]),
            models.Index(fields=["primary_care_physician"]),
            models.Index(fields=["created_at"]),
            models.Index(fields=["hospital", "status", "created_at"]),
            models.Index(fields=["hospital", "primary_care_physician", "status"]),
            models.Index(fields=["hospital", "date_of_birth"]),
            models.Index(fields=["hospital", "gender", "status"]),
            models.Index(fields=["hospital", "city", "state"]),
            models.Index(fields=["hospital", "vip_status"]),
            models.Index(fields=["hospital", "confidential"]),
            models.Index(fields=["hospital", "patient_portal_enrolled"]),
            models.Index(fields=["hospital", "last_name", "first_name", "status"]),
            models.Index(fields=["hospital", "medical_record_number", "status"]),
            models.Index(fields=["hospital", "primary_care_physician", "created_at"]),
        ]
        ordering = ["last_name", "first_name"]

    def __str__(self) -> str:
        return f"{self.last_name}, {self.first_name} (MRN: {self.medical_record_number})"

    def get_full_name(self):
        parts = [self.first_name, self.middle_name, self.last_name, self.suffix]
        return " ".join(part for part in parts if part)

    def get_age(self):
        if not self.date_of_birth:
            return None
        today = date.today()
        return (
            today.year
            - self.date_of_birth.year
            - ((today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day))
        )

    def get_age_at_date(self, reference_date):
        if not self.date_of_birth:
            return None
        return (
            reference_date.year
            - self.date_of_birth.year
            - ((reference_date.month, reference_date.day) < (self.date_of_birth.month, self.date_of_birth.day))
        )

    def is_minor(self):
        return self.get_age() < 18 if self.get_age() is not None else False

    def save(self, *args, **kwargs):
        if not self.medical_record_number:
            import time

            timestamp = str(int(time.time()))
            self.medical_record_number = f"MRN{timestamp[-8:]}"
        super().save(*args, **kwargs)
        self._cache_patient_data()

    def _cache_patient_data(self):
        try:
            patient_data = {
                "id": self.id,
                "uuid": str(self.uuid),
                "medical_record_number": self.medical_record_number,
                "first_name": self.first_name,
                "last_name": self.last_name,
                "date_of_birth": (self.date_of_birth.isoformat() if self.date_of_birth else None),
                "gender": self.gender,
                "status": self.status,
                "hospital_id": self.hospital_id,
                "primary_care_physician_id": self.primary_care_physician_id,
                "full_name": self.get_full_name(),
                "age": self.get_age(),
                "is_minor": self.is_minor(),
                "phone_primary": self.phone_primary,
                "email": self.email,
                "city": self.city,
                "state": self.state,
                "vip_status": self.vip_status,
                "confidential": self.confidential,
                "patient_portal_enrolled": self.patient_portal_enrolled,
            }
            enhanced_cache.cache_patient_data(self.id, patient_data)
        except Exception as e:
            import logging

            logger = logging.getLogger(__name__)
            logger.error(f"Failed to cache patient data for patient {self.id}: {e}")

    @classmethod
    def get_optimized_queryset(cls, hospital_id=None, prefetch_related=None):
        queryset = cls.objects.select_related("primary_care_physician", "hospital", "created_by", "updated_by")
        if prefetch_related:
            queryset = queryset.prefetch_related(*prefetch_related)
        if hospital_id:
            queryset = queryset.filter(hospital_id=hospital_id)
        return queryset

    @classmethod
    def get_cached_patient(cls, patient_id):
        cache_key = enhanced_cache.generate_cache_key("patient", patient_id)
        patient_data = enhanced_cache.cache.get(cache_key)
        if patient_data:
            return patient_data
        try:
            patient = cls.objects.select_related("hospital", "primary_care_physician").get(id=patient_id)
            patient._cache_patient_data()
            return patient
        except cls.DoesNotExist:
            return None

    @classmethod
    def get_patients_by_hospital(cls, hospital_id, status=None, limit=None):
        cache_key = enhanced_cache.generate_cache_key("hospital_patients", hospital_id, status, limit)
        patients = enhanced_cache.cache.get(cache_key)
        if patients:
            return patients
        queryset = cls.get_optimized_queryset(hospital_id)
        if status:
            queryset = queryset.filter(status=status)
        if limit:
            queryset = queryset[:limit]
        patients = list(queryset)
        enhanced_cache.cache.set(cache_key, patients, 300)
        return patients

    @classmethod
    def search_patients(cls, hospital_id, query, limit=50):
        cache_key = enhanced_cache.generate_cache_key("patient_search", hospital_id, query, limit)
        results = enhanced_cache.cache.get(cache_key)
        if results:
            return results
        from django.db.models import Q

        queryset = cls.get_optimized_queryset(hospital_id).filter(
            Q(first_name__icontains=query)
            | Q(last_name__icontains=query)
            | Q(medical_record_number__icontains=query)
            | Q(email__icontains=query)
            | Q(phone_primary__icontains=query)
        )
        results = list(queryset[:limit])
        enhanced_cache.cache.set(cache_key, results, 180)
        return results


class EmergencyContact(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name="emergency_contacts")
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
    phone_primary = EncryptedCharField(max_length=20)
    phone_secondary = EncryptedCharField(max_length=20, blank=True)
    email = EncryptedEmailField(blank=True)
    address_line1 = EncryptedCharField(max_length=255, blank=True)
    address_line2 = EncryptedCharField(max_length=255, blank=True)
    city = models.CharField(max_length=100, blank=True)
    state = models.CharField(max_length=50, blank=True)
    zip_code = models.CharField(max_length=20, blank=True)
    country = models.CharField(max_length=50, default="US")
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
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name="insurance_plans")
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
    effective_date = models.DateField()
    termination_date = models.DateField(null=True, blank=True)
    insurance_company_name = models.CharField(max_length=200)
    insurance_company_address = models.TextField(blank=True)
    insurance_company_phone = models.CharField(max_length=20, blank=True)
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
    copay_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    deductible_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    out_of_pocket_max = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
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
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name="alerts")
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
    is_active = models.BooleanField(default=True)
    requires_acknowledgment = models.BooleanField(default=False)
    acknowledged_by = models.ForeignKey("users.User", on_delete=models.SET_NULL, null=True, blank=True)
    acknowledged_at = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    created_by = models.ForeignKey("users.User", on_delete=models.CASCADE, related_name="created_patient_alerts")
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
