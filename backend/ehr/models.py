import uuid

from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils import timezone
from encrypted_model_fields.fields import EncryptedTextField

from core.models import TenantModel, TimeStampedModel


class EncounterType(models.TextChoices):
    INPATIENT = "INPATIENT", "Inpatient"
    OUTPATIENT = "OUTPATIENT", "Outpatient"
    EMERGENCY = "EMERGENCY", "Emergency"
    URGENT_CARE = "URGENT_CARE", "Urgent Care"
    TELEHEALTH = "TELEHEALTH", "Telehealth"
    HOME_VISIT = "HOME_VISIT", "Home Visit"
    CONSULTATION = "CONSULTATION", "Consultation"
    FOLLOW_UP = "FOLLOW_UP", "Follow-up"
    ANNUAL_PHYSICAL = "ANNUAL_PHYSICAL", "Annual Physical"
    PREVENTIVE = "PREVENTIVE", "Preventive Care"
    SPECIALIST = "SPECIALIST", "Specialist Visit"
    SURGICAL = "SURGICAL", "Surgical Procedure"
    DIAGNOSTIC = "DIAGNOSTIC", "Diagnostic Procedure"
    THERAPY = "THERAPY", "Therapy Session"


class EncounterStatus(models.TextChoices):
    SCHEDULED = "SCHEDULED", "Scheduled"
    IN_PROGRESS = "IN_PROGRESS", "In Progress"
    COMPLETED = "COMPLETED", "Completed"
    CANCELLED = "CANCELLED", "Cancelled"
    NO_SHOW = "NO_SHOW", "No Show"
    RESCHEDULED = "RESCHEDULED", "Rescheduled"


class DispositionType(models.TextChoices):
    DISCHARGED_HOME = "DISCHARGED_HOME", "Discharged Home"
    ADMITTED = "ADMITTED", "Admitted"
    TRANSFERRED = "TRANSFERRED", "Transferred"
    REFERRED = "REFERRED", "Referred"
    FOLLOW_UP = "FOLLOW_UP", "Follow-up Required"
    OBSERVATION = "OBSERVATION", "Observation"
    LEFT_AMA = "LEFT_AMA", "Left Against Medical Advice"
    DECEASED = "DECEASED", "Deceased"


class Encounter(TenantModel):
    """Core encounter/visit record"""

    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)

    # Patient & Provider Information
    patient = models.ForeignKey(
        "patients.Patient", on_delete=models.CASCADE, related_name="encounters"
    )
    primary_physician = models.ForeignKey(
        "users.User",
        on_delete=models.CASCADE,
        related_name="primary_encounters",
        null=True,
    )
    attending_physician = models.ForeignKey(
        "users.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="attending_encounters",
    )
    consulting_physicians = models.ManyToManyField(
        "users.User", blank=True, related_name="consulting_encounters"
    )
    appointment = models.OneToOneField(
        "appointments.Appointment",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )

    # Encounter Details
    encounter_number = models.CharField(max_length=50, db_index=True, default="TEMP")
    encounter_type = models.CharField(
        max_length=20,
        choices=EncounterType.choices,
        default=EncounterType.OUTPATIENT,
    )
    encounter_status = models.CharField(
        max_length=15,
        choices=EncounterStatus.choices,
        default=EncounterStatus.SCHEDULED,
    )

    # Timing
    scheduled_start = models.DateTimeField(default=timezone.now)
    scheduled_end = models.DateTimeField(null=True, blank=True)
    actual_start = models.DateTimeField(null=True, blank=True)
    actual_end = models.DateTimeField(null=True, blank=True)

    # Location
    location = models.CharField(max_length=100, blank=True)
    room = models.CharField(max_length=50, blank=True)
    bed = models.CharField(max_length=50, blank=True)

    # Clinical Information
    chief_complaint = EncryptedTextField(blank=True)
    history_of_present_illness = EncryptedTextField(blank=True)
    diagnosis = EncryptedTextField(blank=True)  # Keep for backward compatibility
    treatment = EncryptedTextField(blank=True)  # Keep for backward compatibility
    prescription_text = EncryptedTextField(
        blank=True
    )  # Keep for backward compatibility
    is_finalized = models.BooleanField(default=False)  # Keep for backward compatibility

    # Disposition
    disposition = models.CharField(
        max_length=20, choices=DispositionType.choices, blank=True
    )
    disposition_notes = EncryptedTextField(blank=True)
    discharge_instructions = EncryptedTextField(blank=True)

    # Administrative
    priority_level = models.CharField(
        max_length=10,
        choices=[
            ("LOW", "Low"),
            ("NORMAL", "Normal"),
            ("HIGH", "High"),
            ("URGENT", "Urgent"),
            ("EMERGENT", "Emergent"),
        ],
        default="NORMAL",
    )

    # Billing & Insurance
    primary_insurance = models.ForeignKey(
        "patients.InsuranceInformation",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="primary_encounters",
    )
    authorization_number = models.CharField(max_length=100, blank=True)

    # System Fields
    created_by = models.ForeignKey(
        "users.User",
        on_delete=models.SET_NULL,
        null=True,
        related_name="created_encounters",
    )
    is_confidential = models.BooleanField(default=False)

    class Meta:
        ordering = ["-scheduled_start"]
        indexes = [
            models.Index(fields=["patient", "-scheduled_start"]),
            models.Index(fields=["primary_physician", "-scheduled_start"]),
            models.Index(fields=["encounter_status"]),
            models.Index(fields=["encounter_type"]),
            models.Index(fields=["encounter_number"]),
        ]

    def __str__(self) -> str:
        date_str = self.scheduled_start.date() if self.scheduled_start else "TBD"
        return f"{self.patient} - {self.encounter_type} on {date_str}"

    def save(self, *args, **kwargs):
        if not self.encounter_number:
            # Generate encounter number if not provided
            import time

            timestamp = str(int(time.time()))
            self.encounter_number = f"ENC{timestamp[-8:]}"
        if not self.scheduled_start and self.appointment:
            self.scheduled_start = self.appointment.start_at
        if not self.scheduled_end and self.appointment:
            self.scheduled_end = self.appointment.end_at
        super().save(*args, **kwargs)


class VitalSigns(models.Model):
    """Patient vital signs recorded during encounters"""

    encounter = models.ForeignKey(
        Encounter, on_delete=models.CASCADE, related_name="vital_signs"
    )

    # Vital Sign Measurements
    systolic_bp = models.PositiveIntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(50), MaxValueValidator(300)],
        help_text="Systolic blood pressure in mmHg",
    )
    diastolic_bp = models.PositiveIntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(30), MaxValueValidator(200)],
        help_text="Diastolic blood pressure in mmHg",
    )
    heart_rate = models.PositiveIntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(20), MaxValueValidator(250)],
        help_text="Heart rate in beats per minute",
    )
    respiratory_rate = models.PositiveIntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(5), MaxValueValidator(100)],
        help_text="Respiratory rate per minute",
    )
    temperature_celsius = models.DecimalField(
        max_digits=4,
        decimal_places=1,
        null=True,
        blank=True,
        validators=[MinValueValidator(30.0), MaxValueValidator(50.0)],
        help_text="Temperature in Celsius",
    )
    oxygen_saturation = models.PositiveIntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(50), MaxValueValidator(100)],
        help_text="Oxygen saturation percentage",
    )
    height_cm = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(30.0), MaxValueValidator(300.0)],
        help_text="Height in centimeters",
    )
    weight_kg = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0.5), MaxValueValidator(1000.0)],
        help_text="Weight in kilograms",
    )
    bmi = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Body Mass Index (calculated)",
    )

    # Pain Assessment
    pain_score = models.PositiveIntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(10)],
        help_text="Pain score (0-10 scale)",
    )
    pain_location = models.CharField(max_length=200, blank=True)

    # Additional Measurements
    head_circumference_cm = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Head circumference in cm (for pediatrics)",
    )

    # Metadata
    recorded_at = models.DateTimeField(default=timezone.now)
    recorded_by = models.ForeignKey("users.User", on_delete=models.CASCADE)
    device_used = models.CharField(max_length=100, blank=True)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ["-recorded_at"]
        indexes = [
            models.Index(fields=["encounter", "-recorded_at"]),
        ]

    def __str__(self):
        return f"{self.encounter} - Vitals {self.recorded_at}"

    def save(self, *args, **kwargs):
        # Calculate BMI if height and weight are available
        if self.height_cm and self.weight_kg:
            height_m = self.height_cm / 100
            self.bmi = self.weight_kg / (height_m * height_m)
        super().save(*args, **kwargs)


class Assessment(models.Model):
    """Clinical assessment and diagnosis"""

    encounter = models.ForeignKey(
        Encounter, on_delete=models.CASCADE, related_name="assessments"
    )

    # Diagnosis Information
    diagnosis_code = models.CharField(
        max_length=20, blank=True, help_text="ICD-10 code"
    )
    diagnosis_description = models.CharField(max_length=500, default="Unknown")
    diagnosis_type = models.CharField(
        max_length=15,
        choices=[
            ("PRIMARY", "Primary Diagnosis"),
            ("SECONDARY", "Secondary Diagnosis"),
            ("WORKING", "Working Diagnosis"),
            ("DIFFERENTIAL", "Differential Diagnosis"),
            ("ADMITTING", "Admitting Diagnosis"),
            ("DISCHARGE", "Discharge Diagnosis"),
        ],
        default="PRIMARY",
    )

    # Clinical Details
    severity = models.CharField(
        max_length=10,
        choices=[
            ("MILD", "Mild"),
            ("MODERATE", "Moderate"),
            ("SEVERE", "Severe"),
            ("CRITICAL", "Critical"),
        ],
        blank=True,
    )
    status = models.CharField(
        max_length=15,
        choices=[
            ("ACTIVE", "Active"),
            ("RESOLVED", "Resolved"),
            ("CHRONIC", "Chronic"),
            ("REMISSION", "In Remission"),
            ("RECURRENT", "Recurrent"),
        ],
        default="ACTIVE",
    )

    # Timeline
    onset_date = models.DateField(null=True, blank=True)
    resolved_date = models.DateField(null=True, blank=True)

    # Provider Information
    diagnosed_by = models.ForeignKey("users.User", on_delete=models.CASCADE)
    confidence_level = models.CharField(
        max_length=10,
        choices=[
            ("LOW", "Low"),
            ("MEDIUM", "Medium"),
            ("HIGH", "High"),
            ("CONFIRMED", "Confirmed"),
        ],
        default="MEDIUM",
    )

    notes = EncryptedTextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["encounter", "diagnosis_type"]),
            models.Index(fields=["diagnosis_code"]),
        ]

    def __str__(self):
        return f"{self.encounter} - {self.diagnosis_description}"


class PlanOfCare(models.Model):
    """Treatment plan and care instructions"""

    encounter = models.ForeignKey(
        Encounter, on_delete=models.CASCADE, related_name="plans"
    )

    plan_type = models.CharField(
        max_length=20,
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
    )

    title = models.CharField(max_length=200)
    description = EncryptedTextField()
    instructions = EncryptedTextField(blank=True)

    # Scheduling
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    frequency = models.CharField(max_length=100, blank=True)

    # Status
    status = models.CharField(
        max_length=15,
        choices=[
            ("ACTIVE", "Active"),
            ("COMPLETED", "Completed"),
            ("CANCELLED", "Cancelled"),
            ("ON_HOLD", "On Hold"),
        ],
        default="ACTIVE",
    )
    priority = models.CharField(
        max_length=10,
        choices=[
            ("LOW", "Low"),
            ("NORMAL", "Normal"),
            ("HIGH", "High"),
            ("URGENT", "Urgent"),
        ],
        default="NORMAL",
    )

    # Provider
    ordered_by = models.ForeignKey("users.User", on_delete=models.CASCADE)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-priority", "-created_at"]
        indexes = [
            models.Index(fields=["encounter", "status"]),
            models.Index(fields=["plan_type"]),
        ]

    def __str__(self):
        return f"{self.encounter} - {self.title}"


class ClinicalNote(models.Model):
    """Progress notes and clinical documentation"""

    encounter = models.ForeignKey(
        Encounter, on_delete=models.CASCADE, related_name="clinical_notes"
    )

    note_type = models.CharField(
        max_length=20,
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
    )

    # SOAP Components (for structured notes)
    subjective = EncryptedTextField(
        blank=True, help_text="Patient's subjective complaints"
    )
    objective = EncryptedTextField(
        blank=True, help_text="Objective findings and observations"
    )
    assessment = EncryptedTextField(
        blank=True, help_text="Clinical assessment and diagnosis"
    )
    plan = EncryptedTextField(blank=True, help_text="Treatment plan and next steps")

    # General Note Content
    content = EncryptedTextField(blank=True, help_text="Free-form note content")

    # Metadata
    author = models.ForeignKey(
        "users.User", on_delete=models.CASCADE, related_name="authored_notes"
    )
    co_signed_by = models.ForeignKey(
        "users.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="cosigned_notes",
    )
    is_signed = models.BooleanField(default=False)
    signed_at = models.DateTimeField(null=True, blank=True)

    # Amendment tracking
    is_amended = models.BooleanField(default=False)
    amendment_reason = models.TextField(blank=True)
    original_note = models.ForeignKey(
        "self", on_delete=models.CASCADE, null=True, blank=True
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["encounter", "-created_at"]),
            models.Index(fields=["author"]),
            models.Index(fields=["note_type"]),
        ]

    def __str__(self):
        return f"{self.encounter} - {self.note_type} by {self.author}"

    def sign_note(self, user):
        if not self.is_signed:
            self.is_signed = True
            self.signed_at = timezone.now()
            self.co_signed_by = user
            self.save()


class Allergy(models.Model):
    """Patient allergies and adverse reactions"""

    patient = models.ForeignKey(
        "patients.Patient", on_delete=models.CASCADE, related_name="allergies"
    )

    # Allergen Information
    allergen = models.CharField(max_length=200)
    allergen_type = models.CharField(
        max_length=20,
        choices=[
            ("MEDICATION", "Medication"),
            ("FOOD", "Food"),
            ("ENVIRONMENTAL", "Environmental"),
            ("CONTACT", "Contact"),
            ("OTHER", "Other"),
        ],
    )

    # Reaction Information
    reaction = models.TextField(help_text="Description of allergic reaction")
    severity = models.CharField(
        max_length=15,
        choices=[
            ("MILD", "Mild"),
            ("MODERATE", "Moderate"),
            ("SEVERE", "Severe"),
            ("LIFE_THREAT", "Life Threatening"),
        ],
    )

    # Timeline
    onset_date = models.DateField(null=True, blank=True)
    verified_date = models.DateField(null=True, blank=True)

    # Status
    status = models.CharField(
        max_length=15,
        choices=[
            ("ACTIVE", "Active"),
            ("INACTIVE", "Inactive"),
            ("RESOLVED", "Resolved"),
            ("UNCONFIRMED", "Unconfirmed"),
        ],
        default="ACTIVE",
    )

    # Provider Information
    reported_by = models.ForeignKey(
        "users.User", on_delete=models.SET_NULL, null=True, blank=True
    )
    verified_by = models.ForeignKey(
        "users.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="verified_allergies",
    )

    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-severity", "allergen"]
        indexes = [
            models.Index(fields=["patient", "status"]),
            models.Index(fields=["allergen_type"]),
        ]
        unique_together = ["patient", "allergen", "allergen_type"]

    def __str__(self):
        return f"{self.patient} - {self.allergen} ({self.severity})"


# Keep for backward compatibility
class EncounterNote(ClinicalNote):
    """Legacy encounter note model - kept for backward compatibility"""

    class Meta:
        proxy = True


def encounter_attachment_upload_to(instance, filename: str) -> str:
    return f"encounters/{instance.encounter_id}/{filename}"


class EncounterAttachment(TimeStampedModel):
    """Files and documents attached to encounters"""

    encounter = models.ForeignKey(
        Encounter, on_delete=models.CASCADE, related_name="attachments"
    )
    file = models.FileField(upload_to=encounter_attachment_upload_to)
    file_type = models.CharField(
        max_length=20,
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
    )
    description = models.CharField(max_length=255, blank=True)
    is_confidential = models.BooleanField(default=False)
    uploaded_by = models.ForeignKey("users.User", on_delete=models.SET_NULL, null=True)

    def __str__(self) -> str:
        return f"{self.encounter} - {self.description or self.file.name}"


class ERTriage(TenantModel):
    """Emergency Room Triage Assessment"""

    encounter = models.OneToOneField(
        Encounter, on_delete=models.CASCADE, related_name="triage"
    )

    # Triage Level (ESI - Emergency Severity Index)
    triage_level = models.CharField(
        max_length=10,
        choices=[
            ("LEVEL_1", "Level 1 - Resuscitation"),
            ("LEVEL_2", "Level 2 - Emergent"),
            ("LEVEL_3", "Level 3 - Urgent"),
            ("LEVEL_4", "Level 4 - Less Urgent"),
            ("LEVEL_5", "Level 5 - Non-urgent"),
        ],
        default="LEVEL_3",
    )

    # Chief Complaint
    chief_complaint = EncryptedTextField(max_length=500)
    onset_time = models.DateTimeField(null=True, blank=True)
    pain_scale = models.PositiveIntegerField(
        null=True, blank=True, validators=[MinValueValidator(0), MaxValueValidator(10)]
    )

    # Vital Signs Snapshot (reference or inline)
    initial_vitals = models.ForeignKey(
        VitalSigns, on_delete=models.SET_NULL, null=True, blank=True
    )

    # Assessment
    mechanism_of_injury = models.TextField(blank=True)
    associated_symptoms = models.JSONField(default=dict, blank=True)
    past_medical_history_relevant = EncryptedTextField(blank=True)

    # Risk Factors
    allergy_status = models.CharField(max_length=20, blank=True)
    medication_compliance = models.BooleanField(default=False)
    recent_surgeries = models.TextField(blank=True)

    # Disposition
    triage_time = models.DateTimeField(auto_now_add=True)
    triage_nurse = models.ForeignKey(
        "users.User",
        on_delete=models.SET_NULL,
        null=True,
        related_name="triage_assessments",
    )
    estimated_wait_time = models.PositiveIntegerField(null=True, blank=True)
    bed_assigned = models.CharField(max_length=50, blank=True)

    # Reassessment
    reassessment_due_at = models.DateTimeField(null=True, blank=True)
    last_reassessed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-triage_time"]
        indexes = [
            models.Index(fields=["encounter", "triage_level"]),
            models.Index(fields=["triage_time"]),
        ]

    def __str__(self):
        return f"Triage {self.triage_level} for {self.encounter.patient} at {self.triage_time}"
