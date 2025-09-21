"""
Comprehensive Test Data Management for HMS System
Provides anonymized healthcare data generation, management, and validation for testing purposes
"""

import pytest
import json
import os
import sys
import uuid
import random
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple, Union, Callable
from pathlib import Path
from dataclasses import dataclass, field
from enum import Enum
import hashlib
import secrets
import string
from decimal import Decimal
import pandas as pd
import numpy as np
from faker import Faker
import django
from django.conf import settings
from django.test import TestCase, TransactionTestCase
from django.db import transaction, DatabaseError
from django.core.management import call_command
from django.core.management.base import CommandError
from django.apps import apps

# Configure Django
if not settings.configured:
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.hms.settings')
    django.setup()

# Import HMS models
from backend.patients.models import Patient, EmergencyContact, InsuranceInformation, PatientAlert
from backend.ehr.models import MedicalRecord, Allergy, Assessment, ClinicalNote, PlanOfCare, Encounter, EncounterAttachment, ERtriage
from backend.appointments.models import Appointment, AppointmentHistory, AppointmentReminder, SurgeryType, OTSlot, OTBooking
from backend.billing.models import Bill, ServiceCatalog, Discount, DepartmentBudget
from backend.pharmacy.models import Medication, MedicationBatch, Manufacturer
from backend.lab.models import LabResult
from backend.users.models import Department, UserCredential, UserLoginHistory
from backend.hospitals.models import Hospital, HospitalPlan
from backend.facilities.models import Facility
from backend.hr.models import Employee, Department as HRDepartment
from backend.accounting.models import Account, Transaction, JournalEntry, AccountingAuditLog
from backend.analytics.models import Analytics
from backend.feedback.models import Feedback, Survey
from backend.core.models import AuditLog, Notification, QualityMetric

# Healthcare encryption and compliance
from backend.core.encryption import EncryptionManager
from backend.core.audit import AuditManager
from backend.core.compliance import ComplianceManager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DataAnonymizationLevel(Enum):
    """Levels of data anonymization"""
    FULL = "full"          # Complete anonymization, no real data
    PARTIAL = "partial"    # Some real data patterns, but no real PHI
    SYNTHETIC = "synthetic" # Realistic synthetic data
    OBSCURED = "obscured"   # Real data with sensitive parts obscured

class TestDataType(Enum):
    """Types of test data"""
    PATIENT = "patient"
    MEDICAL_RECORD = "medical_record"
    APPOINTMENT = "appointment"
    BILLING = "billing"
    PHARMACY = "pharmacy"
    LAB_RESULT = "lab_result"
    USER = "user"
    HOSPITAL = "hospital"
    FACILITY = "facility"
    EMPLOYEE = "employee"
    INSURANCE = "insurance"
    EMERGENCY = "emergency"

@dataclass
class TestDataConfig:
    """Configuration for test data generation"""
    anonymization_level: DataAnonymizationLevel = DataAnonymizationLevel.SYNTHETIC
    data_volume: str = "medium"  # small, medium, large
    healthcare_compliance: bool = True
    include_encrypted_fields: bool = True
    include_audit_trail: bool = True
    include_relationships: bool = True
    data_validation: bool = True
    locale: str = "en_US"
    seed: Optional[int] = None

@dataclass
class TestDataGenerationRequest:
    """Request for test data generation"""
    data_types: List[TestDataType]
    count: int
    config: TestDataConfig
    relationships: Dict[str, Any] = field(default_factory=dict)
    custom_fields: Dict[str, Any] = field(default_factory=dict)
    output_format: str = "django_models"  # django_models, json, csv

@dataclass
class TestDataGenerationResult:
    """Result of test data generation"""
    success: bool
    generated_count: int
    data: List[Any]
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    file_paths: List[str] = field(default_factory=list)

class HealthcareDataGenerator:
    """Healthcare-specific test data generator"""

    def __init__(self, config: TestDataConfig):
        self.config = config
        self.faker = Faker(config.locale)
        if config.seed:
            self.faker.seed_instance(config.seed)
            random.seed(config.seed)
            np.random.seed(config.seed)

        # Healthcare components
        self.encryption_manager = EncryptionManager()
        self.audit_manager = AuditManager()
        self.compliance_manager = ComplianceManager()

        # Medical data generators
        self.icd10_codes = self._load_icd10_codes()
        self.medications = self._load_medications()
        self.procedures = self._load_procedures()
        self.laboratory_tests = self._load_laboratory_tests()

        # Generated data cache
        self.generated_data = {}
        self.relationship_map = {}

    def _load_icd10_codes(self) -> List[str]:
        """Load ICD-10 codes for diagnosis generation"""
        return [
            "I10", "E11.9", "J45.909", "M54.5", "F41.1", "E66.9", "I25.1", "J44.9",
            "N18.9", "M10.9", "K21.9", "D50.9", "H40.9", "M54.2", "E78.5",
            "I48.91", "N39.0", "K25.7", "J44.1", "G47.33", "M06.9", "E87.0"
        ]

    def _load_medications(self) -> List[Dict[str, Any]]:
        """Load medication data"""
        return [
            {"name": "Lisinopril", "strength": "10mg", "form": "tablet"},
            {"name": "Metformin", "strength": "500mg", "form": "tablet"},
            {"name": "Atorvastatin", "strength": "20mg", "form": "tablet"},
            {"name": "Amlodipine", "strength": "5mg", "form": "tablet"},
            {"name": "Omeprazole", "strength": "20mg", "form": "capsule"},
            {"name": "Sertraline", "strength": "50mg", "form": "tablet"},
            {"name": "Metoprolol", "strength": "25mg", "form": "tablet"},
            {"name": "Losartan", "strength": "50mg", "form": "tablet"},
            {"name": "Gabapentin", "strength": "300mg", "form": "capsule"},
            {"name": "Albuterol", "strength": "90mcg", "form": "inhaler"}
        ]

    def _load_procedures(self) -> List[str]:
        """Load medical procedure data"""
        return [
            "Complete Blood Count", "Comprehensive Metabolic Panel", "Lipid Panel",
            "Hemoglobin A1C", "Chest X-Ray", "EKG", "Stress Test", "Colonoscopy",
            "Mammogram", "Pap Smear", "PSA Test", "Bone Density Scan", "MRI",
            "CT Scan", "Ultrasound", "Echocardiogram", "Pulmonary Function Test"
        ]

    def _load_laboratory_tests(self) -> List[str]:
        """Load laboratory test data"""
        return [
            "Complete Blood Count", "Comprehensive Metabolic Panel", "Lipid Panel",
            "Thyroid Stimulating Hormone", "Hemoglobin A1C", "Vitamin D",
            "Complete Urinalysis", "C-Reactive Protein", "Prothrombin Time",
            "International Normalized Ratio", "Basic Metabolic Panel", "Liver Function Test"
        ]

    def generate_test_data(self, request: TestDataGenerationRequest) -> TestDataGenerationResult:
        """Generate test data based on request"""
        result = TestDataGenerationResult(
            success=False,
            generated_count=0,
            data=[],
            metadata={
                'request_type': request.data_types,
                'requested_count': request.count,
                'anonymization_level': request.config.anonymization_level.value,
                'generation_time': datetime.now().isoformat()
            }
        )

        try:
            # Validate request
            self._validate_request(request)

            # Generate data for each type
            for data_type in request.data_types:
                logger.info(f"Generating {data_type.value} data...")
                type_result = self._generate_data_type(data_type, request.count, request.config)

                if type_result.success:
                    result.data.extend(type_result.data)
                    result.generated_count += type_result.generated_count
                    result.metadata[f"{data_type.value}_count"] = type_result.generated_count
                else:
                    result.errors.extend(type_result.errors)

            # Establish relationships if requested
            if request.config.include_relationships and request.relationships:
                self._establish_relationships(result.data, request.relationships)

            # Apply data validation
            if request.config.data_validation:
                validation_result = self._validate_generated_data(result.data)
                result.warnings.extend(validation_result.get('warnings', []))

            # Save data if requested
            if request.output_format != "django_models":
                save_result = self._save_generated_data(result.data, request.output_format)
                result.file_paths = save_result.get('file_paths', [])

            result.success = len(result.errors) == 0

        except Exception as e:
            result.errors.append(f"Data generation failed: {str(e)}")
            logger.error(f"Test data generation failed: {str(e)}")

        return result

    def _validate_request(self, request: TestDataGenerationRequest):
        """Validate data generation request"""
        if not request.data_types:
            raise ValueError("At least one data type must be specified")

        if request.count <= 0:
            raise ValueError("Count must be greater than 0")

        if request.count > 10000 and request.config.data_volume == "small":
            raise ValueError("Count too large for small data volume")

    def _generate_data_type(self, data_type: TestDataType, count: int, config: TestDataConfig) -> TestDataGenerationResult:
        """Generate data for a specific type"""
        result = TestDataGenerationResult(
            success=False,
            generated_count=0,
            data=[],
            metadata={'data_type': data_type.value}
        )

        try:
            if data_type == TestDataType.PATIENT:
                result = self._generate_patients(count, config)
            elif data_type == TestDataType.MEDICAL_RECORD:
                result = self._generate_medical_records(count, config)
            elif data_type == TestDataType.APPOINTMENT:
                result = self._generate_appointments(count, config)
            elif data_type == TestDataType.BILLING:
                result = self._generate_bills(count, config)
            elif data_type == TestDataType.PHARMACY:
                result = self._generate_pharmacy_data(count, config)
            elif data_type == TestDataType.LAB_RESULT:
                result = self._generate_lab_results(count, config)
            elif data_type == TestDataType.USER:
                result = self._generate_users(count, config)
            elif data_type == TestDataType.HOSPITAL:
                result = self._generate_hospitals(count, config)
            elif data_type == TestDataType.FACILITY:
                result = self._generate_facilities(count, config)
            elif data_type == TestDataType.EMPLOYEE:
                result = self._generate_employees(count, config)
            elif data_type == TestDataType.INSURANCE:
                result = self._generate_insurance_data(count, config)
            elif data_type == TestDataType.EMERGENCY:
                result = self._generate_emergency_data(count, config)
            else:
                raise ValueError(f"Unknown data type: {data_type}")

        except Exception as e:
            result.errors.append(f"Failed to generate {data_type.value}: {str(e)}")
            logger.error(f"Failed to generate {data_type.value} data: {str(e)}")

        return result

    def _generate_patients(self, count: int, config: TestDataConfig) -> TestDataGenerationResult:
        """Generate patient test data"""
        result = TestDataGenerationResult(
            success=False,
            generated_count=0,
            data=[],
            metadata={'data_type': 'patient'}
        )

        try:
            patients = []
            used_mrns = set()
            used_emails = set()

            for i in range(count):
                patient_data = self._generate_patient_data(i, config, used_mrns, used_emails)
                patients.append(patient_data)

            # Create Django model instances
            if config.output_format == "django_models":
                patient_models = []
                for patient_data in patients:
                    try:
                        patient = Patient(**patient_data)
                        patient_models.append(patient)
                    except Exception as e:
                        result.warnings.append(f"Failed to create patient model: {str(e)}")

                result.data = patient_models
                result.generated_count = len(patient_models)
            else:
                result.data = patients
                result.generated_count = len(patients)

            result.success = True

        except Exception as e:
            result.errors.append(f"Patient generation failed: {str(e)}")

        return result

    def _generate_patient_data(self, index: int, config: TestDataConfig, used_mrns: set, used_emails: set) -> Dict[str, Any]:
        """Generate individual patient data"""
        # Generate unique identifiers
        medical_record_number = self._generate_unique_mrn(index, used_mrns)
        email = self._generate_unique_email(index, used_emails)

        # Generate basic demographics
        gender = random.choice(['M', 'F', 'Other'])
        date_of_birth = self._generate_date_of_birth(gender)

        patient_data = {
            'first_name': self._generate_first_name(gender),
            'last_name': self._generate_last_name(),
            'email': email,
            'phone': self._generate_phone_number(),
            'date_of_birth': date_of_birth,
            'gender': gender,
            'blood_type': random.choice(['A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-']),
            'medical_record_number': medical_record_number,
            'ssn': self._generate_ssn(),
            'address': self._generate_address(),
            'emergency_contact_name': self._generate_emergency_contact_name(),
            'emergency_contact_phone': self._generate_phone_number(),
            'primary_care_physician': self._generate_physician_name(),
            'insurance_provider': random.choice([
                'Blue Cross Blue Shield', 'Aetna', 'UnitedHealth', 'Cigna', 'Humana',
                'Kaiser Permanente', 'Medicare', 'Medicaid'
            ]),
            'insurance_policy_number': self._generate_policy_number(),
            'allergies': self._generate_allergies(),
            'medications': self._generate_medications_list(),
            'chronic_conditions': self._generate_chronic_conditions(),
            'last_visit_date': self._generate_last_visit_date(),
            'status': random.choice(['active', 'inactive', 'deceased']),
            'created_at': datetime.now() - timedelta(days=random.randint(1, 365)),
            'updated_at': datetime.now()
        }

        # Apply encryption for sensitive fields
        if config.include_encrypted_fields:
            sensitive_fields = ['first_name', 'last_name', 'email', 'phone', 'ssn', 'address']
            for field in sensitive_fields:
                if field in patient_data and patient_data[field]:
                    patient_data[field] = self.encryption_manager.encrypt(str(patient_data[field]))

        return patient_data

    def _generate_medical_records(self, count: int, config: TestDataConfig) -> TestDataGenerationResult:
        """Generate medical record test data"""
        result = TestDataGenerationResult(
            success=False,
            generated_count=0,
            data=[],
            metadata={'data_type': 'medical_record'}
        )

        try:
            records = []

            # Get existing patients or generate some
            if 'patient' in self.generated_data:
                patients = self.generated_data['patient']
            else:
                patient_request = TestDataGenerationRequest(
                    data_types=[TestDataType.PATIENT],
                    count=min(count, 100),  # Limit patient generation
                    config=config
                )
                patient_result = self._generate_patients(patient_request.count, config)
                patients = patient_result.data
                self.generated_data['patient'] = patients

            for i in range(count):
                if patients:
                    patient = random.choice(patients)
                    patient_id = getattr(patient, 'id', i + 1)  # Use index if no id
                else:
                    patient_id = i + 1

                record_data = self._generate_medical_record_data(patient_id, i, config)
                records.append(record_data)

            # Create Django model instances
            if config.output_format == "django_models":
                record_models = []
                for record_data in records:
                    try:
                        record = MedicalRecord(**record_data)
                        record_models.append(record)
                    except Exception as e:
                        result.warnings.append(f"Failed to create medical record model: {str(e)}")

                result.data = record_models
                result.generated_count = len(record_models)
            else:
                result.data = records
                result.generated_count = len(records)

            result.success = True

        except Exception as e:
            result.errors.append(f"Medical record generation failed: {str(e)}")

        return result

    def _generate_medical_record_data(self, patient_id: int, index: int, config: TestDataConfig) -> Dict[str, Any]:
        """Generate individual medical record data"""
        record_types = ['diagnosis', 'treatment', 'follow-up', 'lab_result', 'procedure', 'consultation']
        record_type = random.choice(record_types)

        record_data = {
            'patient_id': patient_id,
            'record_date': self._generate_record_date(),
            'record_type': record_type,
            'diagnosis': self._generate_diagnosis(),
            'treatment': self._generate_treatment(),
            'notes': self._generate_medical_notes(),
            'physician_id': random.randint(1, 50),
            'facility_id': random.randint(1, 10),
            'is_confidential': random.random() < 0.1,  # 10% are confidential
            'created_at': datetime.now() - timedelta(days=random.randint(1, 365)),
            'updated_at': datetime.now()
        }

        # Apply encryption for sensitive fields
        if config.include_encrypted_fields:
            sensitive_fields = ['diagnosis', 'treatment', 'notes']
            for field in sensitive_fields:
                if field in record_data and record_data[field]:
                    record_data[field] = self.encryption_manager.encrypt(str(record_data[field]))

        return record_data

    def _generate_appointments(self, count: int, config: TestDataConfig) -> TestDataGenerationResult:
        """Generate appointment test data"""
        result = TestDataGenerationResult(
            success=False,
            generated_count=0,
            data=[],
            metadata={'data_type': 'appointment'}
        )

        try:
            appointments = []

            # Get existing patients or generate some
            if 'patient' not in self.generated_data:
                patient_request = TestDataGenerationRequest(
                    data_types=[TestDataType.PATIENT],
                    count=min(count, 100),
                    config=config
                )
                patient_result = self._generate_patients(patient_request.count, config)
                self.generated_data['patient'] = patient_result.data

            patients = self.generated_data['patient']

            for i in range(count):
                if patients:
                    patient = random.choice(patients)
                    patient_id = getattr(patient, 'id', i + 1)
                else:
                    patient_id = i + 1

                appointment_data = self._generate_appointment_data(patient_id, i, config)
                appointments.append(appointment_data)

            # Create Django model instances
            if config.output_format == "django_models":
                appointment_models = []
                for appointment_data in appointments:
                    try:
                        appointment = Appointment(**appointment_data)
                        appointment_models.append(appointment)
                    except Exception as e:
                        result.warnings.append(f"Failed to create appointment model: {str(e)}")

                result.data = appointment_models
                result.generated_count = len(appointment_models)
            else:
                result.data = appointments
                result.generated_count = len(appointments)

            result.success = True

        except Exception as e:
            result.errors.append(f"Appointment generation failed: {str(e)}")

        return result

    def _generate_appointment_data(self, patient_id: int, index: int, config: TestDataConfig) -> Dict[str, Any]:
        """Generate individual appointment data"""
        appointment_types = ['consultation', 'follow-up', 'procedure', 'emergency', 'routine_checkup', 'specialist_referral']
        appointment_type = random.choice(appointment_types)

        appointment_data = {
            'patient_id': patient_id,
            'appointment_date': self._generate_appointment_date(),
            'appointment_time': self._generate_appointment_time(),
            'appointment_type': appointment_type,
            'status': random.choice(['scheduled', 'confirmed', 'completed', 'cancelled', 'no_show']),
            'physician_id': random.randint(1, 50),
            'facility_id': random.randint(1, 10),
            'duration': random.randint(15, 120),  # minutes
            'notes': self._generate_appointment_notes(),
            'reminder_sent': random.random() < 0.8,  # 80% have reminders sent
            'created_at': datetime.now() - timedelta(days=random.randint(1, 30)),
            'updated_at': datetime.now()
        }

        return appointment_data

    def _generate_bills(self, count: int, config: TestDataConfig) -> TestDataGenerationResult:
        """Generate billing test data"""
        result = TestDataGenerationResult(
            success=False,
            generated_count=0,
            data=[],
            metadata={'data_type': 'billing'}
        )

        try:
            bills = []

            # Get existing patients or generate some
            if 'patient' not in self.generated_data:
                patient_request = TestDataGenerationRequest(
                    data_types=[TestDataType.PATIENT],
                    count=min(count, 100),
                    config=config
                )
                patient_result = self._generate_patients(patient_request.count, config)
                self.generated_data['patient'] = patient_result.data

            patients = self.generated_data['patient']

            for i in range(count):
                if patients:
                    patient = random.choice(patients)
                    patient_id = getattr(patient, 'id', i + 1)
                else:
                    patient_id = i + 1

                bill_data = self._generate_bill_data(patient_id, i, config)
                bills.append(bill_data)

            # Create Django model instances
            if config.output_format == "django_models":
                bill_models = []
                for bill_data in bills:
                    try:
                        bill = Bill(**bill_data)
                        bill_models.append(bill)
                    except Exception as e:
                        result.warnings.append(f"Failed to create bill model: {str(e)}")

                result.data = bill_models
                result.generated_count = len(bill_models)
            else:
                result.data = bills
                result.generated_count = len(bills)

            result.success = True

        except Exception as e:
            result.errors.append(f"Bill generation failed: {str(e)}")

        return result

    def _generate_bill_data(self, patient_id: int, index: int, config: TestDataConfig) -> Dict[str, Any]:
        """Generate individual bill data"""
        services = [
            {'name': 'Office Visit', 'cost': Decimal('150.00')},
            {'name': 'Laboratory Tests', 'cost': Decimal('200.00')},
            {'name': 'X-Ray', 'cost': Decimal('300.00')},
            {'name': 'Specialist Consultation', 'cost': Decimal('250.00')},
            {'name': 'Procedure', 'cost': Decimal('500.00')},
            {'name': 'Emergency Room', 'cost': Decimal('1000.00')}
        ]

        service = random.choice(services)
        total_amount = service['cost'] * Decimal(random.uniform(0.8, 1.5))

        bill_data = {
            'patient_id': patient_id,
            'bill_date': datetime.now().date() - timedelta(days=random.randint(0, 90)),
            'due_date': datetime.now().date() + timedelta(days=random.randint(15, 60)),
            'total_amount': total_amount,
            'amount_paid': Decimal('0.00') if random.random() < 0.3 else total_amount * Decimal(random.uniform(0.1, 0.9)),
            'status': random.choice(['pending', 'paid', 'overdue', 'disputed', 'cancelled']),
            'payment_method': random.choice(['cash', 'credit_card', 'insurance', 'check']),
            'insurance_info': self._generate_insurance_info(),
            'description': f"{service['name']} - {service['name']}",
            'created_at': datetime.now() - timedelta(days=random.randint(1, 90)),
            'updated_at': datetime.now()
        }

        # Apply encryption for sensitive fields
        if config.include_encrypted_fields:
            sensitive_fields = ['payment_method', 'insurance_info']
            for field in sensitive_fields:
                if field in bill_data and bill_data[field]:
                    bill_data[field] = self.encryption_manager.encrypt(str(bill_data[field]))

        return bill_data

    def _generate_pharmacy_data(self, count: int, config: TestDataConfig) -> TestDataGenerationResult:
        """Generate pharmacy test data"""
        result = TestDataGenerationResult(
            success=False,
            generated_count=0,
            data=[],
            metadata={'data_type': 'pharmacy'}
        )

        try:
            medications = []

            for i in range(count):
                medication_data = self._generate_medication_data(i, config)
                medications.append(medication_data)

            # Create Django model instances
            if config.output_format == "django_models":
                medication_models = []
                for medication_data in medications:
                    try:
                        medication = Medication(**medication_data)
                        medication_models.append(medication)
                    except Exception as e:
                        result.warnings.append(f"Failed to create medication model: {str(e)}")

                result.data = medication_models
                result.generated_count = len(medication_models)
            else:
                result.data = medications
                result.generated_count = len(medications)

            result.success = True

        except Exception as e:
            result.errors.append(f"Pharmacy data generation failed: {str(e)}")

        return result

    def _generate_medication_data(self, index: int, config: TestDataConfig) -> Dict[str, Any]:
        """Generate individual medication data"""
        medication_info = random.choice(self.medications)

        medication_data = {
            'name': medication_info['name'],
            'strength': medication_info['strength'],
            'form': medication_info['form'],
            'description': f"{medication_info['name']} {medication_info['strength']}",
            'category': random.choice(['antibiotic', 'painkiller', 'antihypertensive', 'diabetic', 'antidepressant']),
            'requires_prescription': True,
            'controlled_substance': random.random() < 0.1,  # 10% are controlled
            'manufacturer': random.choice(['Pfizer', 'Johnson & Johnson', 'Novartis', 'Merck', 'GSK']),
            'ndc_code': self._generate_ndc_code(),
            'active_ingredients': medication_info['name'],
            'dosage_instructions': f"Take {medication_info['strength']} {'once daily' if 'daily' in medication_info['strength'] else 'twice daily'}",
            'side_effects': self._generate_side_effects(),
            'interactions': self._generate_interactions(),
            'created_at': datetime.now() - timedelta(days=random.randint(1, 365)),
            'updated_at': datetime.now()
        }

        return medication_data

    def _generate_lab_results(self, count: int, config: TestDataConfig) -> TestDataGenerationResult:
        """Generate lab result test data"""
        result = TestDataGenerationResult(
            success=False,
            generated_count=0,
            data=[],
            metadata={'data_type': 'lab_result'}
        )

        try:
            lab_results = []

            # Get existing patients or generate some
            if 'patient' not in self.generated_data:
                patient_request = TestDataGenerationRequest(
                    data_types=[TestDataType.PATIENT],
                    count=min(count, 100),
                    config=config
                )
                patient_result = self._generate_patients(patient_request.count, config)
                self.generated_data['patient'] = patient_result.data

            patients = self.generated_data['patient']

            for i in range(count):
                if patients:
                    patient = random.choice(patients)
                    patient_id = getattr(patient, 'id', i + 1)
                else:
                    patient_id = i + 1

                lab_result_data = self._generate_lab_result_data(patient_id, i, config)
                lab_results.append(lab_result_data)

            # Create Django model instances
            if config.output_format == "django_models":
                lab_result_models = []
                for lab_result_data in lab_results:
                    try:
                        lab_result = LabResult(**lab_result_data)
                        lab_result_models.append(lab_result)
                    except Exception as e:
                        result.warnings.append(f"Failed to create lab result model: {str(e)}")

                result.data = lab_result_models
                result.generated_count = len(lab_result_models)
            else:
                result.data = lab_results
                result.generated_count = len(lab_results)

            result.success = True

        except Exception as e:
            result.errors.append(f"Lab result generation failed: {str(e)}")

        return result

    def _generate_lab_result_data(self, patient_id: int, index: int, config: TestDataConfig) -> Dict[str, Any]:
        """Generate individual lab result data"""
        test_name = random.choice(self.laboratory_tests)

        # Generate realistic lab values
        lab_values = {
            'Complete Blood Count': {
                'WBC': f"{random.uniform(4.0, 11.0):.1f} K/μL",
                'RBC': f"{random.uniform(4.2, 5.9):.1f} M/μL",
                'Hemoglobin': f"{random.uniform(12.0, 16.0):.1f} g/dL",
                'Hematocrit': f"{random.uniform(36.0, 48.0):.1f}%",
                'Platelets': f"{random.uniform(150, 450):.0f} K/μL"
            },
            'Comprehensive Metabolic Panel': {
                'Glucose': f"{random.uniform(70, 100):.0f} mg/dL",
                'BUN': f"{random.uniform(7, 20):.0f} mg/dL",
                'Creatinine': f"{random.uniform(0.6, 1.3):.2f} mg/dL",
                'Sodium': f"{random.uniform(135, 145):.0f} mmol/L",
                'Potassium': f"{random.uniform(3.5, 5.0):.1f} mmol/L",
                'Chloride': f"{random.uniform(96, 106):.0f} mmol/L",
                'CO2': f"{random.uniform(23, 29):.0f} mmol/L"
            }
        }

        test_values = lab_values.get(test_name, {'Result': f"{random.uniform(0, 100):.1f}"})

        lab_result_data = {
            'patient_id': patient_id,
            'test_date': datetime.now().date() - timedelta(days=random.randint(0, 30)),
            'test_name': test_name,
            'result_value': json.dumps(test_values),
            'result_text': self._generate_lab_result_text(test_values),
            'reference_range': self._generate_reference_range(test_name),
            'is_abnormal': random.random() < 0.2,  # 20% are abnormal
            'units': self._generate_lab_units(test_name),
            'ordering_physician': random.randint(1, 50),
            'facility_id': random.randint(1, 10),
            'status': random.choice(['completed', 'pending', 'cancelled']),
            'created_at': datetime.now() - timedelta(days=random.randint(1, 30)),
            'updated_at': datetime.now()
        }

        return lab_result_data

    def _generate_users(self, count: int, config: TestDataConfig) -> TestDataGenerationResult:
        """Generate user test data"""
        result = TestDataGenerationResult(
            success=False,
            generated_count=0,
            data=[],
            metadata={'data_type': 'user'}
        )

        try:
            users = []

            user_types = ['admin', 'physician', 'nurse', 'staff', 'receptionist', 'billing_specialist']

            for i in range(count):
                user_data = self._generate_user_data(i, config, user_types)
                users.append(user_data)

            # Create Django model instances
            if config.output_format == "django_models":
                user_models = []
                for user_data in users:
                    try:
                        from django.contrib.auth.models import User
                        user = User(**user_data)
                        user_models.append(user)
                    except Exception as e:
                        result.warnings.append(f"Failed to create user model: {str(e)}")

                result.data = user_models
                result.generated_count = len(user_models)
            else:
                result.data = users
                result.generated_count = len(users)

            result.success = True

        except Exception as e:
            result.errors.append(f"User generation failed: {str(e)}")

        return result

    def _generate_user_data(self, index: int, config: TestDataConfig, user_types: List[str]) -> Dict[str, Any]:
        """Generate individual user data"""
        user_type = random.choice(user_types)

        user_data = {
            'username': f"{user_type}_{index:04d}",
            'first_name': self._generate_first_name(),
            'last_name': self._generate_last_name(),
            'email': self._generate_unique_email(index, set()),
            'is_active': True,
            'is_staff': user_type in ['admin', 'staff'],
            'is_superuser': user_type == 'admin',
            'date_joined': datetime.now() - timedelta(days=random.randint(1, 365)),
            'last_login': datetime.now() - timedelta(days=random.randint(0, 30)) if random.random() < 0.7 else None
        }

        return user_data

    def _generate_hospitals(self, count: int, config: TestDataConfig) -> TestDataGenerationResult:
        """Generate hospital test data"""
        result = TestDataGenerationResult(
            success=False,
            generated_count=0,
            data=[],
            metadata={'data_type': 'hospital'}
        )

        try:
            hospitals = []

            for i in range(count):
                hospital_data = self._generate_hospital_data(i, config)
                hospitals.append(hospital_data)

            # Create Django model instances
            if config.output_format == "django_models":
                hospital_models = []
                for hospital_data in hospitals:
                    try:
                        hospital = Hospital(**hospital_data)
                        hospital_models.append(hospital)
                    except Exception as e:
                        result.warnings.append(f"Failed to create hospital model: {str(e)}")

                result.data = hospital_models
                result.generated_count = len(hospital_models)
            else:
                result.data = hospitals
                result.generated_count = len(hospitals)

            result.success = True

        except Exception as e:
            result.errors.append(f"Hospital generation failed: {str(e)}")

        return result

    def _generate_hospital_data(self, index: int, config: TestDataConfig) -> Dict[str, Any]:
        """Generate individual hospital data"""
        hospital_types = ['general', 'specialty', 'childrens', 'teaching', 'rehabilitation']
        hospital_type = random.choice(hospital_types)

        hospital_data = {
            'name': f"{self.faker.company()} {'Medical Center' if hospital_type == 'general' else hospital_type.title()}",
            'address': self._generate_address(),
            'phone': self._generate_phone_number(),
            'email': f"info@hospital{index:04d}.com",
            'type': hospital_type,
            'bed_count': random.randint(50, 1000),
            'emergency_services': random.random() < 0.8,  # 80% have emergency services
            'operating_rooms': random.randint(1, 20),
            'icu_beds': random.randint(5, 50),
            'created_at': datetime.now() - timedelta(days=random.randint(1, 365)),
            'updated_at': datetime.now()
        }

        return hospital_data

    def _generate_facilities(self, count: int, config: TestDataConfig) -> TestDataGenerationResult:
        """Generate facility test data"""
        result = TestDataGenerationResult(
            success=False,
            generated_count=0,
            data=[],
            metadata={'data_type': 'facility'}
        )

        try:
            facilities = []

            for i in range(count):
                facility_data = self._generate_facility_data(i, config)
                facilities.append(facility_data)

            # Create Django model instances
            if config.output_format == "django_models":
                facility_models = []
                for facility_data in facilities:
                    try:
                        facility = Facility(**facility_data)
                        facility_models.append(facility)
                    except Exception as e:
                        result.warnings.append(f"Failed to create facility model: {str(e)}")

                result.data = facility_models
                result.generated_count = len(facility_models)
            else:
                result.data = facilities
                result.generated_count = len(facilities)

            result.success = True

        except Exception as e:
            result.errors.append(f"Facility generation failed: {str(e)}")

        return result

    def _generate_facility_data(self, index: int, config: TestDataConfig) -> Dict[str, Any]:
        """Generate individual facility data"""
        facility_types = ['clinic', 'laboratory', 'imaging_center', 'pharmacy', 'rehabilitation_center']
        facility_type = random.choice(facility_types)

        facility_data = {
            'name': f"{self.faker.company()} {facility_type.replace('_', ' ').title()}",
            'address': self._generate_address(),
            'phone': self._generate_phone_number(),
            'email': f"contact@facility{index:04d}.com",
            'type': facility_type,
            'capacity': random.randint(10, 100),
            'operating_hours': self._generate_operating_hours(),
            'services_offered': self._generate_services_offered(facility_type),
            'created_at': datetime.now() - timedelta(days=random.randint(1, 365)),
            'updated_at': datetime.now()
        }

        return facility_data

    def _generate_employees(self, count: int, config: TestDataConfig) -> TestDataGenerationResult:
        """Generate employee test data"""
        result = TestDataGenerationResult(
            success=False,
            generated_count=0,
            data=[],
            metadata={'data_type': 'employee'}
        )

        try:
            employees = []

            for i in range(count):
                employee_data = self._generate_employee_data(i, config)
                employees.append(employee_data)

            # Create Django model instances
            if config.output_format == "django_models":
                employee_models = []
                for employee_data in employees:
                    try:
                        employee = Employee(**employee_data)
                        employee_models.append(employee)
                    except Exception as e:
                        result.warnings.append(f"Failed to create employee model: {str(e)}")

                result.data = employee_models
                result.generated_count = len(employee_models)
            else:
                result.data = employees
                result.generated_count = len(employees)

            result.success = True

        except Exception as e:
            result.errors.append(f"Employee generation failed: {str(e)}")

        return result

    def _generate_employee_data(self, index: int, config: TestDataConfig) -> Dict[str, Any]:
        """Generate individual employee data"""
        positions = ['Physician', 'Nurse', 'Administrator', 'Technician', 'Therapist', 'Specialist']
        position = random.choice(positions)

        employee_data = {
            'first_name': self._generate_first_name(),
            'last_name': self._generate_last_name(),
            'email': self._generate_unique_email(index, set()),
            'phone': self._generate_phone_number(),
            'position': position,
            'department': random.choice(['Cardiology', 'Emergency', 'Pediatrics', 'Surgery', 'Administration']),
            'hire_date': datetime.now() - timedelta(days=random.randint(30, 3650)),
            'salary': Decimal(random.uniform(50000, 250000)),
            'employee_id': f"EMP{index:06d}",
            'license_number': self._generate_license_number(),
            'specialty': self._generate_specialty(position),
            'created_at': datetime.now() - timedelta(days=random.randint(1, 365)),
            'updated_at': datetime.now()
        }

        return employee_data

    def _generate_insurance_data(self, count: int, config: TestDataConfig) -> TestDataGenerationResult:
        """Generate insurance test data"""
        result = TestDataGenerationResult(
            success=False,
            generated_count=0,
            data=[],
            metadata={'data_type': 'insurance'}
        )

        try:
            insurance_data_list = []

            for i in range(count):
                insurance_info = self._generate_insurance_info_data(i, config)
                insurance_data_list.append(insurance_info)

            # Create Django model instances
            if config.output_format == "django_models":
                insurance_models = []
                for insurance_info in insurance_data_list:
                    try:
                        insurance = InsuranceInformation(**insurance_info)
                        insurance_models.append(insurance)
                    except Exception as e:
                        result.warnings.append(f"Failed to create insurance model: {str(e)}")

                result.data = insurance_models
                result.generated_count = len(insurance_models)
            else:
                result.data = insurance_data_list
                result.generated_count = len(insurance_data_list)

            result.success = True

        except Exception as e:
            result.errors.append(f"Insurance data generation failed: {str(e)}")

        return result

    def _generate_insurance_info_data(self, index: int, config: TestDataConfig) -> Dict[str, Any]:
        """Generate individual insurance data"""
        insurance_providers = [
            'Blue Cross Blue Shield', 'Aetna', 'UnitedHealthcare', 'Cigna', 'Humana',
            'Kaiser Permanente', 'Anthem', 'Molina Healthcare', 'Centene', 'WellCare'
        ]

        insurance_data = {
            'provider_name': random.choice(insurance_providers),
            'policy_number': self._generate_policy_number(),
            'group_number': self._generate_group_number(),
            'subscriber_id': self._generate_subscriber_id(),
            'coverage_start_date': datetime.now() - timedelta(days=random.randint(30, 365)),
            'coverage_end_date': datetime.now() + timedelta(days=random.randint(30, 365)),
            'coverage_type': random.choice(['HMO', 'PPO', 'EPO', 'POS']),
            'deductible': Decimal(random.uniform(500, 5000)),
            'copay': Decimal(random.uniform(10, 100)),
            'out_of_pocket_max': Decimal(random.uniform(1000, 10000)),
            'created_at': datetime.now() - timedelta(days=random.randint(1, 365)),
            'updated_at': datetime.now()
        }

        return insurance_data

    def _generate_emergency_data(self, count: int, config: TestDataConfig) -> TestDataGenerationResult:
        """Generate emergency test data"""
        result = TestDataGenerationResult(
            success=False,
            generated_count=0,
            data=[],
            metadata={'data_type': 'emergency'}
        )

        try:
            emergency_data_list = []

            # Get existing patients or generate some
            if 'patient' not in self.generated_data:
                patient_request = TestDataGenerationRequest(
                    data_types=[TestDataType.PATIENT],
                    count=min(count, 100),
                    config=config
                )
                patient_result = self._generate_patients(patient_request.count, config)
                self.generated_data['patient'] = patient_result.data

            patients = self.generated_data['patient']

            for i in range(count):
                if patients:
                    patient = random.choice(patients)
                    patient_id = getattr(patient, 'id', i + 1)
                else:
                    patient_id = i + 1

                emergency_info = self._generate_emergency_info_data(patient_id, i, config)
                emergency_data_list.append(emergency_info)

            # Create Django model instances
            if config.output_format == "django_models":
                emergency_models = []
                for emergency_info in emergency_data_list:
                    try:
                        emergency = ERtriage(**emergency_info)
                        emergency_models.append(emergency)
                    except Exception as e:
                        result.warnings.append(f"Failed to create emergency model: {str(e)}")

                result.data = emergency_models
                result.generated_count = len(emergency_models)
            else:
                result.data = emergency_data_list
                result.generated_count = len(emergency_data_list)

            result.success = True

        except Exception as e:
            result.errors.append(f"Emergency data generation failed: {str(e)}")

        return result

    def _generate_emergency_info_data(self, patient_id: int, index: int, config: TestDataConfig) -> Dict[str, Any]:
        """Generate individual emergency data"""
        triage_levels = ['critical', 'urgent', 'semi-urgent', 'non-urgent']
        triage_level = random.choice(triage_levels)

        emergency_data = {
            'patient_id': patient_id,
            'arrival_date': datetime.now() - timedelta(hours=random.randint(1, 24)),
            'triage_level': triage_level,
            'chief_complaint': self._generate_chief_complaint(),
            'vital_signs': self._generate_vital_signs(),
            'initial_assessment': self._generate_initial_assessment(),
            'disposition': random.choice(['admitted', 'discharged', 'transferred', 'left_without_being_seen']),
            'length_of_stay': random.randint(1, 72),  # hours
            'created_at': datetime.now() - timedelta(hours=random.randint(1, 24)),
            'updated_at': datetime.now()
        }

        return emergency_data

    # Helper methods for data generation
    def _generate_unique_mrn(self, index: int, used_mrns: set) -> str:
        """Generate unique medical record number"""
        while True:
            mrn = f"MRN{random.randint(10000000, 99999999)}"
            if mrn not in used_mrns:
                used_mrns.add(mrn)
                return mrn

    def _generate_unique_email(self, index: int, used_emails: set) -> str:
        """Generate unique email address"""
        while True:
            email = f"patient{index:04d}@example.com"
            if email not in used_emails:
                used_emails.add(email)
                return email

    def _generate_first_name(self, gender: str = None) -> str:
        """Generate first name"""
        if gender == 'M':
            return random.choice(['James', 'John', 'Robert', 'Michael', 'William', 'David', 'Richard', 'Joseph', 'Thomas', 'Charles'])
        elif gender == 'F':
            return random.choice(['Mary', 'Patricia', 'Jennifer', 'Linda', 'Elizabeth', 'Barbara', 'Susan', 'Jessica', 'Sarah', 'Karen'])
        else:
            return self.faker.first_name()

    def _generate_last_name(self) -> str:
        """Generate last name"""
        return self.faker.last_name()

    def _generate_phone_number(self) -> str:
        """Generate phone number"""
        return f"({random.randint(200, 999)}) {random.randint(100, 999)}-{random.randint(1000, 9999)}"

    def _generate_date_of_birth(self, gender: str) -> datetime:
        """Generate realistic date of birth"""
        # Generate age between 0 and 90
        age = random.randint(0, 90)
        date_of_birth = datetime.now() - timedelta(days=age * 365)

        # Adjust for gender-based life expectancy differences
        if gender == 'M':
            date_of_birth -= timedelta(days=random.randint(0, 365 * 5))

        return date_of_birth

    def _generate_ssn(self) -> str:
        """Generate SSN-like identifier (not real SSN)"""
        return f"{random.randint(100, 999)}-{random.randint(10, 99)}-{random.randint(1000, 9999)}"

    def _generate_address(self) -> str:
        """Generate address"""
        return f"{self.faker.street_address()}, {self.faker.city()}, {self.faker.state_abbr()} {self.faker.zipcode()}"

    def _generate_emergency_contact_name(self) -> str:
        """Generate emergency contact name"""
        return f"{self._generate_first_name()} {self._generate_last_name()}"

    def _generate_physician_name(self) -> str:
        """Generate physician name"""
        return f"Dr. {self._generate_first_name()} {self._generate_last_name()}"

    def _generate_policy_number(self) -> str:
        """Generate insurance policy number"""
        return f"POL{random.randint(100000000, 999999999)}"

    def _generate_allergies(self) -> str:
        """Generate allergies list"""
        allergies = ['Penicillin', 'Sulfa drugs', 'NSAIDs', 'Latex', 'Shellfish', 'Nuts', 'Dairy', 'Eggs']
        selected_allergies = random.sample(allergies, random.randint(0, 3))
        return ', '.join(selected_allergies) if selected_allergies else 'None'

    def _generate_medications_list(self) -> str:
        """Generate medications list"""
        medications = ['Lisinopril', 'Metformin', 'Atorvastatin', 'Amlodipine', 'Omeprazole']
        selected_medications = random.sample(medications, random.randint(0, 4))
        return ', '.join(selected_medications) if selected_medications else 'None'

    def _generate_chronic_conditions(self) -> str:
        """Generate chronic conditions"""
        conditions = ['Hypertension', 'Diabetes Type 2', 'Asthma', 'Arthritis', 'Heart Disease', 'Depression']
        selected_conditions = random.sample(conditions, random.randint(0, 3))
        return ', '.join(selected_conditions) if selected_conditions else 'None'

    def _generate_last_visit_date(self) -> datetime:
        """Generate last visit date"""
        return datetime.now() - timedelta(days=random.randint(0, 365))

    def _generate_record_date(self) -> datetime:
        """Generate medical record date"""
        return datetime.now() - timedelta(days=random.randint(0, 365))

    def _generate_diagnosis(self) -> str:
        """Generate diagnosis"""
        return f"{random.choice(self.icd10_codes)}: {self.faker.sentence()}"

    def _generate_treatment(self) -> str:
        """Generate treatment"""
        treatments = ['Medication therapy', 'Physical therapy', 'Surgery', 'Lifestyle changes', 'Monitoring']
        return f"{random.choice(treatments)}: {self.faker.sentence()}"

    def _generate_medical_notes(self) -> str:
        """Generate medical notes"""
        return self.faker.paragraph(nb_sentences=random.randint(2, 5))

    def _generate_appointment_date(self) -> datetime.date:
        """Generate appointment date"""
        return datetime.now().date() + timedelta(days=random.randint(-30, 90))

    def _generate_appointment_time(self) -> datetime.time:
        """Generate appointment time"""
        hour = random.randint(8, 17)
        minute = random.choice([0, 15, 30, 45])
        return datetime.time(hour, minute)

    def _generate_appointment_notes(self) -> str:
        """Generate appointment notes"""
        return self.faker.sentence()

    def _generate_insurance_info(self) -> str:
        """Generate insurance information"""
        return f"{random.choice(['Blue Cross', 'Aetna', 'UnitedHealth'])} Policy: {self._generate_policy_number()}"

    def _generate_ndc_code(self) -> str:
        """Generate NDC code"""
        return f"{random.randint(1000, 9999)}-{random.randint(1000, 9999)}-{random.randint(10, 99)}"

    def _generate_side_effects(self) -> str:
        """Generate side effects"""
        effects = ['Dizziness', 'Nausea', 'Headache', 'Drowsiness', 'Dry mouth', 'Constipation']
        selected_effects = random.sample(effects, random.randint(0, 3))
        return ', '.join(selected_effects) if selected_effects else 'None'

    def _generate_interactions(self) -> str:
        """Generate drug interactions"""
        return self.faker.sentence()

    def _generate_lab_result_text(self, values: Dict[str, str]) -> str:
        """Generate lab result text"""
        result_lines = []
        for key, value in values.items():
            result_lines.append(f"{key}: {value}")
        return '\n'.join(result_lines)

    def _generate_reference_range(self, test_name: str) -> str:
        """Generate reference range"""
        ranges = {
            'Complete Blood Count': 'Normal ranges apply',
            'Comprehensive Metabolic Panel': 'Normal ranges apply',
            'Lipid Panel': 'Normal ranges apply'
        }
        return ranges.get(test_name, 'Normal ranges apply')

    def _generate_lab_units(self, test_name: str) -> str:
        """Generate lab units"""
        return 'Standard units'

    def _generate_operating_hours(self) -> str:
        """Generate operating hours"""
        return f"{random.randint(6, 9)}:00 AM - {random.randint(5, 9)}:00 PM"

    def _generate_services_offered(self, facility_type: str) -> str:
        """Generate services offered"""
        services = {
            'clinic': 'General practice, vaccinations, health screenings',
            'laboratory': 'Blood tests, urinalysis, diagnostic testing',
            'imaging_center': 'X-rays, CT scans, MRI, ultrasound',
            'pharmacy': 'Prescription filling, medication counseling, vaccinations',
            'rehabilitation_center': 'Physical therapy, occupational therapy, speech therapy'
        }
        return services.get(facility_type, 'Various health services')

    def _generate_license_number(self) -> str:
        """Generate license number"""
        return f"LIC{random.randint(100000, 999999)}"

    def _generate_specialty(self, position: str) -> str:
        """Generate medical specialty"""
        specialties = {
            'Physician': ['Cardiology', 'Neurology', 'Orthopedics', 'Pediatrics', 'Internal Medicine'],
            'Nurse': ['Registered Nurse', 'Nurse Practitioner', 'Licensed Practical Nurse'],
            'Technician': ['Radiology Technician', 'Laboratory Technician', 'Surgical Technician'],
            'Therapist': ['Physical Therapist', 'Occupational Therapist', 'Respiratory Therapist'],
            'Specialist': ['Anesthesiologist', 'Radiologist', 'Pathologist', 'Surgeon']
        }
        position_specialties = specialties.get(position, ['General Practice'])
        return random.choice(position_specialties)

    def _generate_group_number(self) -> str:
        """Generate insurance group number"""
        return f"GRP{random.randint(100000, 999999)}"

    def _generate_subscriber_id(self) -> str:
        """Generate subscriber ID"""
        return f"SUB{random.randint(100000000, 999999999)}"

    def _generate_chief_complaint(self) -> str:
        """Generate chief complaint"""
        complaints = [
            'Chest pain', 'Shortness of breath', 'Abdominal pain', 'Headache',
            'Fever', 'Nausea/vomiting', 'Back pain', 'Injury', 'Dizziness', 'Weakness'
        ]
        return random.choice(complaints)

    def _generate_vital_signs(self) -> str:
        """Generate vital signs"""
        return json.dumps({
            'blood_pressure': f"{random.randint(90, 180)}/{random.randint(60, 110)}",
            'heart_rate': f"{random.randint(60, 120)} bpm",
            'respiratory_rate': f"{random.randint(12, 24)} rpm",
            'temperature': f"{random.uniform(96.0, 104.0):.1f}°F",
            'oxygen_saturation': f"{random.randint(88, 100)}%"
        })

    def _generate_initial_assessment(self) -> str:
        """Generate initial assessment"""
        return self.faker.paragraph(nb_sentences=random.randint(2, 4))

    # Data management methods
    def _establish_relationships(self, data: List[Any], relationships: Dict[str, Any]):
        """Establish relationships between generated data"""
        # This method would establish foreign key relationships
        # between different data types (e.g., link patients to appointments)
        pass

    def _validate_generated_data(self, data: List[Any]) -> Dict[str, Any]:
        """Validate generated data for consistency and compliance"""
        validation_result = {'warnings': []}

        # Check for data consistency
        if len(data) == 0:
            validation_result['warnings'].append("No data generated")

        # Check for missing required fields
        # This would be model-specific

        # Check for data compliance
        if self.config.healthcare_compliance:
            validation_result['warnings'].extend(self._check_healthcare_compliance(data))

        return validation_result

    def _check_healthcare_compliance(self, data: List[Any]) -> List[str]:
        """Check healthcare compliance requirements"""
        warnings = []

        # Check PHI protection
        # Check data retention policies
        # Check consent requirements

        return warnings

    def _save_generated_data(self, data: List[Any], output_format: str) -> Dict[str, Any]:
        """Save generated data to files"""
        file_paths = []
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        try:
            if output_format == "json":
                # Convert to dict format
                data_dict = []
                for item in data:
                    if hasattr(item, '__dict__'):
                        data_dict.append(item.__dict__)
                    else:
                        data_dict.append(item)

                filename = f"/tmp/test_data_{timestamp}.json"
                with open(filename, 'w') as f:
                    json.dump(data_dict, f, indent=2, default=str)
                file_paths.append(filename)

            elif output_format == "csv":
                # Convert to DataFrame
                df = pd.DataFrame([item.__dict__ if hasattr(item, '__dict__') else item for item in data])
                filename = f"/tmp/test_data_{timestamp}.csv"
                df.to_csv(filename, index=False)
                file_paths.append(filename)

        except Exception as e:
            warnings.warn(f"Failed to save data: {str(e)}")

        return {'file_paths': file_paths}

# Test classes
class TestHealthcareDataGeneration(TestCase):
    """Test healthcare data generation"""

    def setUp(self):
        """Setup test environment"""
        self.config = TestDataConfig(
            anonymization_level=DataAnonymizationLevel.SYNTHETIC,
            data_volume="small",
            healthcare_compliance=True,
            include_encrypted_fields=True,
            seed=12345
        )
        self.generator = HealthcareDataGenerator(self.config)

    def test_patient_data_generation(self):
        """Test patient data generation"""
        request = TestDataGenerationRequest(
            data_types=[TestDataType.PATIENT],
            count=10,
            config=self.config
        )

        result = self.generator.generate_test_data(request)

        self.assertTrue(result.success)
        self.assertEqual(result.generated_count, 10)
        self.assertEqual(len(result.errors), 0)
        self.assertEqual(len(result.data), 10)

        # Check patient data structure
        if result.data:
            patient = result.data[0]
            required_fields = ['first_name', 'last_name', 'email', 'medical_record_number']
            for field in required_fields:
                self.assertTrue(hasattr(patient, field) or field in patient)

    def test_medical_record_generation(self):
        """Test medical record generation"""
        request = TestDataGenerationRequest(
            data_types=[TestDataType.MEDICAL_RECORD],
            count=5,
            config=self.config
        )

        result = self.generator.generate_test_data(request)

        self.assertTrue(result.success)
        self.assertEqual(result.generated_count, 5)

    def test_appointment_generation(self):
        """Test appointment generation"""
        request = TestDataGenerationRequest(
            data_types=[TestDataType.APPOINTMENT],
            count=15,
            config=self.config
        )

        result = self.generator.generate_test_data(request)

        self.assertTrue(result.success)
        self.assertEqual(result.generated_count, 15)

    def test_billing_generation(self):
        """Test billing generation"""
        request = TestDataGenerationRequest(
            data_types=[TestDataType.BILLING],
            count=8,
            config=self.config
        )

        result = self.generator.generate_test_data(request)

        self.assertTrue(result.success)
        self.assertEqual(result.generated_count, 8)

    def test_comprehensive_data_generation(self):
        """Test comprehensive data generation with multiple types"""
        request = TestDataGenerationRequest(
            data_types=[
                TestDataType.PATIENT,
                TestDataType.MEDICAL_RECORD,
                TestDataType.APPOINTMENT,
                TestDataType.BILLING
            ],
            count=5,
            config=self.config,
            include_relationships=True
        )

        result = self.generator.generate_test_data(request)

        self.assertTrue(result.success)
        self.assertGreater(result.generated_count, 0)

        # Check that all data types were generated
        expected_types = ['patient', 'medical_record', 'appointment', 'billing']
        for data_type in expected_types:
            count_key = f"{data_type}_count"
            self.assertIn(count_key, result.metadata)
            self.assertGreater(result.metadata[count_key], 0)

    def test_encryption_integration(self):
        """Test encryption integration"""
        config = TestDataConfig(
            anonymization_level=DataAnonymizationLevel.SYNTHETIC,
            include_encrypted_fields=True,
            seed=12345
        )
        generator = HealthcareDataGenerator(config)

        request = TestDataGenerationRequest(
            data_types=[TestDataType.PATIENT],
            count=3,
            config=config
        )

        result = generator.generate_test_data(request)

        self.assertTrue(result.success)

        # Check that sensitive fields are encrypted
        if result.data:
            patient = result.data[0]
            if hasattr(patient, 'first_name'):
                # Encrypted fields should not be plaintext
                self.assertNotEqual(patient.first_name, 'Test0000')

    def test_data_validation(self):
        """Test data validation"""
        request = TestDataGenerationRequest(
            data_types=[TestDataType.PATIENT],
            count=5,
            config=self.config,
            data_validation=True
        )

        result = self.generator.generate_test_data(request)

        self.assertTrue(result.success)

        # Check for validation warnings
        # This would depend on specific validation rules

    def test_data_export(self):
        """Test data export functionality"""
        request = TestDataGenerationRequest(
            data_types=[TestDataType.PATIENT],
            count=5,
            config=self.config,
            output_format="json"
        )

        result = self.generator.generate_test_data(request)

        self.assertTrue(result.success)
        self.assertGreater(len(result.file_paths), 0)

        # Check that files were created
        for file_path in result.file_paths:
            self.assertTrue(os.path.exists(file_path))

# Data management utilities
class TestDataManager:
    """Test data management utilities"""

    def __init__(self, config: TestDataConfig = None):
        self.config = config or TestDataConfig()
        self.generator = HealthcareDataGenerator(self.config)
        self.generated_data_cache = {}
        self.data_files = []

    def create_test_dataset(self, name: str, data_types: List[TestDataType], count: int) -> Dict[str, Any]:
        """Create a named test dataset"""
        request = TestDataGenerationRequest(
            data_types=data_types,
            count=count,
            config=self.config
        )

        result = self.generator.generate_test_data(request)

        if result.success:
            self.generated_data_cache[name] = result.data

        return {
            'name': name,
            'success': result.success,
            'data_count': result.generated_count,
            'data_types': [dt.value for dt in data_types],
            'errors': result.errors,
            'warnings': result.warnings
        }

    def load_test_dataset(self, name: str) -> Optional[List[Any]]:
        """Load a previously created test dataset"""
        return self.generated_data_cache.get(name)

    def cleanup_test_data(self):
        """Clean up all generated test data"""
        # Clean up cached data
        self.generated_data_cache.clear()

        # Clean up data files
        for file_path in self.data_files:
            try:
                if os.path.exists(file_path):
                    os.remove(file_path)
            except Exception as e:
                logger.warning(f"Failed to cleanup file {file_path}: {str(e)}")

        self.data_files = []

    def create_healthcare_test_suite(self) -> Dict[str, Any]:
        """Create comprehensive healthcare test suite"""
        test_suite = {
            'name': 'healthcare_comprehensive',
            'datasets': {}
        }

        # Create various datasets
        datasets = [
            ('patients', [TestDataType.PATIENT], 100),
            ('medical_records', [TestDataType.MEDICAL_RECORD], 200),
            ('appointments', [TestDataType.APPOINTMENT], 150),
            ('billing', [TestDataType.BILLING], 120),
            ('pharmacy', [TestDataType.PHARMACY], 80),
            ('lab_results', [TestDataType.LAB_RESULT], 180),
            ('emergency', [TestDataType.EMERGENCY], 50)
        ]

        for dataset_name, data_types, count in datasets:
            dataset_info = self.create_test_dataset(dataset_name, data_types, count)
            test_suite['datasets'][dataset_name] = dataset_info

        return test_suite

# Main execution
if __name__ == "__main__":
    # Create test data manager
    manager = TestDataManager()

    # Create comprehensive test suite
    test_suite = manager.create_healthcare_test_suite()

    print("Healthcare test data generation completed")
    print(f"Generated {len(test_suite['datasets'])} datasets")

    for dataset_name, dataset_info in test_suite['datasets'].items():
        print(f"- {dataset_name}: {dataset_info['data_count']} records")

    # Run tests
    import django
    from django.test.utils import get_runner

    django.setup()
    test_runner = get_runner(settings)()
    failures = test_runner.run_tests(['__main__'])

    if failures:
        print(f"❌ {failures} test(s) failed")
        exit(1)
    else:
        print("✅ All tests passed")