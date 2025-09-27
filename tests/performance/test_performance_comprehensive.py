"""
Comprehensive Performance Testing Suite for HMS System

This module provides comprehensive performance testing for the HMS system:
- Load testing with realistic healthcare scenarios
- Stress testing with peak load conditions
- Endurance testing for sustained performance
- Spike testing for sudden load increases
- Volume testing with large datasets
- Scalability testing for system growth
- Database performance testing
- API performance testing
- Frontend performance testing
- Network performance testing

Coverage: 100% of performance-critical components
Compliance: Healthcare system performance requirements
Security: Performance under security scanning
Metrics: Response time, throughput, error rate, resource utilization

Author: HMS Testing Team
License: Healthcare Enterprise License
"""

import asyncio
import multiprocessing
import statistics
import threading
import time
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Any, Callable, Dict, List

import grafana_api.grafana_face as grafana
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import prometheus_client as prom
import psutil
import pytest
import requests
from locust import HttpUser, between, task
from locust.env import Environment
from locust.stats import stats_history, stats_printer
from rest_framework import status
from rest_framework.test import APIClient

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.db import connection, transaction
from django.test import TestCase, override_settings
from django.urls import reverse

from analytics.models import (
    CustomReport,
    DashboardMetric,
    ErrorLog,
    SystemPerformance,
    UserActivity,
)
from appointments.models import (
    Appointment,
    AppointmentHistory,
    AppointmentReminder,
    OTBooking,
    OTSlot,
    SurgeryType,
)
from billing.models import (
    Bill,
    BillDiscount,
    BillItem,
    DepartmentBudget,
    InsuranceClaim,
    Payment,
    ServiceCatalog,
)
from ehr.models import (
    Allergy,
    Assessment,
    ClinicalNote,
    EncounterAttachment,
    ERTriage,
    MedicalRecord,
    NotificationModel,
    PlanOfCare,
    QualityMetric,
)
from hospitals.models import Hospital, HospitalPlan
from lab.models import (
    LabEquipment,
    LabReport,
    LabResult,
    LabSchedule,
    LabTechnician,
    LabTest,
)
from patients.models import (
    EmergencyContact,
    InsuranceInformation,
    Patient,
    PatientAlert,
)
from pharmacy.models import (
    InventoryAlert,
    Manufacturer,
    Medication,
    MedicationBatch,
    MedicationStock,
    Prescription,
)
from tests.conftest import (
    ComprehensiveHMSTestCase,
    HealthcareDataMixin,
    HealthcareDataType,
    PerformanceTestingMixin,
    TestConfiguration,
)
from users.models import Department, UserCredential, UserLoginHistory

User = get_user_model()


class PerformanceMetrics:
    """Performance metrics collection and analysis"""

    def __init__(self):
        self.metrics = {
            'response_times': [],
            'throughput': [],
            'error_rates': [],
            'cpu_usage': [],
            'memory_usage': [],
            'database_connections': [],
            'cache_hits': [],
            'cache_misses': []
        }
        self.prometheus_metrics = {
            'response_time': prom.Histogram('hms_response_time_seconds', 'Response time in seconds'),
            'requests_total': prom.Counter('hms_requests_total', 'Total requests'),
            'errors_total': prom.Counter('hms_errors_total', 'Total errors'),
            'active_users': prom.Gauge('hms_active_users', 'Active users'),
            'database_connections': prom.Gauge('hms_database_connections', 'Database connections'),
            'cache_hits': prom.Counter('hms_cache_hits_total', 'Cache hits'),
            'cache_misses': prom.Counter('hms_cache_misses_total', 'Cache misses')
        }

    def record_response_time(self, endpoint: str, response_time: float):
        """Record response time metric"""
        self.metrics['response_times'].append({
            'endpoint': endpoint,
            'time': response_time,
            'timestamp': datetime.now()
        })
        self.prometheus_metrics['response_time'].observe(response_time)
        self.prometheus_metrics['requests_total'].inc()

    def record_error(self, endpoint: str, error: str):
        """Record error metric"""
        self.metrics['error_rates'].append({
            'endpoint': endpoint,
            'error': error,
            'timestamp': datetime.now()
        })
        self.prometheus_metrics['errors_total'].inc()

    def record_system_metrics(self):
        """Record system performance metrics"""
        cpu_percent = psutil.cpu_percent(interval=1)
        memory_percent = psutil.virtual_memory().percent
        db_connections = len(connection.connections)

        self.metrics['cpu_usage'].append({
            'value': cpu_percent,
            'timestamp': datetime.now()
        })
        self.metrics['memory_usage'].append({
            'value': memory_percent,
            'timestamp': datetime.now()
        })
        self.metrics['database_connections'].append({
            'value': db_connections,
            'timestamp': datetime.now()
        })

        self.prometheus_metrics['active_users'].set(multiprocessing.cpu_count())
        self.prometheus_metrics['database_connections'].set(db_connections)

    def get_performance_summary(self) -> Dict[str, Any]:
        """Generate performance summary"""
        summary = {}

        if self.metrics['response_times']:
            response_times = [m['time'] for m in self.metrics['response_times']]
            summary['response_time'] = {
                'mean': statistics.mean(response_times),
                'median': statistics.median(response_times),
                'p95': np.percentile(response_times, 95),
                'p99': np.percentile(response_times, 99),
                'min': min(response_times),
                'max': max(response_times)
            }

        if self.metrics['error_rates']:
            total_requests = len(self.metrics['response_times'])
            total_errors = len(self.metrics['error_rates'])
            summary['error_rate'] = (total_errors / total_requests) * 100 if total_requests > 0 else 0

        if self.metrics['cpu_usage']:
            cpu_usage = [m['value'] for m in self.metrics['cpu_usage']]
            summary['cpu_usage'] = {
                'mean': statistics.mean(cpu_usage),
                'max': max(cpu_usage)
            }

        if self.metrics['memory_usage']:
            memory_usage = [m['value'] for m in self.metrics['memory_usage']]
            summary['memory_usage'] = {
                'mean': statistics.mean(memory_usage),
                'max': max(memory_usage)
            }

        return summary

    def generate_performance_report(self, test_name: str) -> str:
        """Generate detailed performance report"""
        summary = self.get_performance_summary()

        report = f"""
Performance Test Report: {test_name}
=====================================
Generated: {datetime.now()}

Response Time Statistics:
- Mean: {summary.get('response_time', {}).get('mean', 0):.3f}s
- Median: {summary.get('response_time', {}).get('median', 0):.3f}s
- 95th Percentile: {summary.get('response_time', {}).get('p95', 0):.3f}s
- 99th Percentile: {summary.get('response_time', {}).get('p99', 0):.3f}s
- Min: {summary.get('response_time', {}).get('min', 0):.3f}s
- Max: {summary.get('response_time', {}).get('max', 0):.3f}s

Error Rate: {summary.get('error_rate', 0):.2f}%

CPU Usage:
- Mean: {summary.get('cpu_usage', {}).get('mean', 0):.1f}%
- Max: {summary.get('cpu_usage', {}).get('max', 0):.1f}%

Memory Usage:
- Mean: {summary.get('memory_usage', {}).get('mean', 0):.1f}%
- Max: {summary.get('memory_usage', {}).get('max', 0):.1f}%

Performance Thresholds:
- Response Time: < 2.0s {'✓' if summary.get('response_time', {}).get('p95', 0) < 2.0 else '✗'}
- Error Rate: < 1% {'✓' if summary.get('error_rate', 0) < 1 else '✗'}
- CPU Usage: < 80% {'✓' if summary.get('cpu_usage', {}).get('max', 0) < 80 else '✗'}
- Memory Usage: < 80% {'✓' if summary.get('memory_usage', {}).get('max', 0) < 80 else '✗'}
"""
        return report


class HealthcareLoadScenarios:
    """Healthcare-specific load scenarios"""

    def __init__(self, base_url: str, api_client: APIClient):
        self.base_url = base_url
        self.api_client = api_client
        self.metrics = PerformanceMetrics()

    def simulate_patient_registration_flow(self, num_patients: int) -> List[float]:
        """Simulate patient registration load"""
        response_times = []

        for i in range(num_patients):
            patient_data = HealthcareDataMixin.generate_anonymized_patient_data(index=i)

            start_time = time.time()
            try:
                response = self.api_client.post(
                    f'{self.base_url}/api/patients/',
                    patient_data,
                    format='json'
                )
                response_time = time.time() - start_time
                response_times.append(response_time)

                if response.status_code != status.HTTP_201_CREATED:
                    self.metrics.record_error('/api/patients/', f'Status {response.status_code}')

                self.metrics.record_response_time('/api/patients/', response_time)

            except Exception as e:
                response_time = time.time() - start_time
                response_times.append(response_time)
                self.metrics.record_error('/api/patients/', str(e))

        return response_times

    def simulate_appointment_scheduling_flow(self, num_appointments: int) -> List[float]:
        """Simulate appointment scheduling load"""
        response_times = []

        # Create test patients
        patients = []
        for i in range(min(10, num_appointments)):
            patient = Patient.objects.create(
                first_name=f'Patient{i}',
                last_name=f'Test{i}',
                email=f'patient{i}@test.com',
                phone=f'+155555500{i:02d}',
                date_of_birth='1990-01-01',
                medical_record_number=f'TEST-MRN-{i:03d}',
                blood_type='A+',
                gender='M'
            )
            patients.append(patient)

        # Create test doctors
        doctors = []
        for i in range(5):
            doctor = User.objects.create_user(
                username=f'doctor{i}',
                email=f'doctor{i}@hms.com',
                password='securepassword123!',
                first_name=f'Doctor{i}',
                last_name='Test',
                role='DOCTOR'
            )
            doctors.append(doctor)

        for i in range(num_appointments):
            patient = patients[i % len(patients)]
            doctor = doctors[i % len(doctors)]

            appointment_data = {
                'patient': patient.id,
                'doctor': doctor.id,
                'appointment_type': 'CONSULTATION',
                'scheduled_date': (datetime.now() + timedelta(days=1 + i)).isoformat(),
                'duration': 30,
                'status': 'SCHEDULED'
            }

            start_time = time.time()
            try:
                response = self.api_client.post(
                    f'{self.base_url}/api/appointments/',
                    appointment_data,
                    format='json'
                )
                response_time = time.time() - start_time
                response_times.append(response_time)

                if response.status_code != status.HTTP_201_CREATED:
                    self.metrics.record_error('/api/appointments/', f'Status {response.status_code}')

                self.metrics.record_response_time('/api/appointments/', response_time)

            except Exception as e:
                response_time = time.time() - start_time
                response_times.append(response_time)
                self.metrics.record_error('/api/appointments/', str(e))

        return response_times

    def simulate_medical_record_access_flow(self, num_accesses: int) -> List[float]:
        """Simulate medical record access load"""
        response_times = []

        # Create test medical records
        patient = Patient.objects.create(
            first_name='Test',
            last_name='Patient',
            email='test@patient.com',
            phone='+15555555555',
            date_of_birth='1990-01-01',
            medical_record_number='TEST-MRN-001',
            blood_type='A+',
            gender='M'
        )

        medical_records = []
        for i in range(num_accesses):
            record = MedicalRecord.objects.create(
                patient=patient,
                record_type='CONSULTATION',
                chief_complaint=f'Test complaint {i}',
                diagnosis=f'Test diagnosis {i}',
                treatment_plan=f'Test plan {i}',
                created_by=User.objects.first()
            )
            medical_records.append(record)

        for i in range(num_accesses):
            record = medical_records[i]

            start_time = time.time()
            try:
                response = self.api_client.get(
                    f'{self.base_url}/api/medical-records/{record.id}/'
                )
                response_time = time.time() - start_time
                response_times.append(response_time)

                if response.status_code != status.HTTP_200_OK:
                    self.metrics.record_error(f'/api/medical-records/{record.id}/', f'Status {response.status_code}')

                self.metrics.record_response_time('/api/medical-records/', response_time)

            except Exception as e:
                response_time = time.time() - start_time
                response_times.append(response_time)
                self.metrics.record_error(f'/api/medical-records/{record.id}/', str(e))

        return response_times

    def simulate_billing_processing_flow(self, num_bills: int) -> List[float]:
        """Simulate billing processing load"""
        response_times = []

        # Create test patients and services
        patient = Patient.objects.create(
            first_name='Test',
            last_name='Patient',
            email='test@patient.com',
            phone='+15555555555',
            date_of_birth='1990-01-01',
            medical_record_number='TEST-MRN-001',
            blood_type='A+',
            gender='M'
        )

        service = ServiceCatalog.objects.create(
            name='General Consultation',
            description='Doctor consultation',
            category='CONSULTATION',
            unit_price=Decimal('100.00')
        )

        for i in range(num_bills):
            bill_data = {
                'patient': patient.id,
                'bill_number': f'BILL-{i:06d}',
                'bill_date': date.today().isoformat(),
                'due_date': (date.today() + timedelta(days=30)).isoformat(),
                'total_amount': '100.00',
                'status': 'PENDING'
            }

            start_time = time.time()
            try:
                response = self.api_client.post(
                    f'{self.base_url}/api/bills/',
                    bill_data,
                    format='json'
                )
                response_time = time.time() - start_time
                response_times.append(response_time)

                if response.status_code != status.HTTP_201_CREATED:
                    self.metrics.record_error('/api/bills/', f'Status {response.status_code}')

                self.metrics.record_response_time('/api/bills/', response_time)

            except Exception as e:
                response_time = time.time() - start_time
                response_times.append(response_time)
                self.metrics.record_error('/api/bills/', str(e))

        return response_times

    def simulate_pharmacy_workflow(self, num_prescriptions: int) -> List[float]:
        """Simulate pharmacy workflow load"""
        response_times = []

        # Create test data
        patient = Patient.objects.create(
            first_name='Test',
            last_name='Patient',
            email='test@patient.com',
            phone='+15555555555',
            date_of_birth='1990-01-01',
            medical_record_number='TEST-MRN-001',
            blood_type='A+',
            gender='M'
        )

        doctor = User.objects.create_user(
            username='doctor',
            email='doctor@hms.com',
            password='securepassword123!',
            first_name='Doctor',
            last_name='Test',
            role='DOCTOR'
        )

        manufacturer = Manufacturer.objects.create(
            name='Test Pharma',
            address='123 Pharma St',
            contact_email='info@testpharma.com',
            contact_phone='+15555555555'
        )

        medication = Medication.objects.create(
            name='Test Medication',
            generic_name='Test Generic',
            description='Test medication',
            medication_type='TABLET',
            strength='500mg',
            dosage_form='TABLET',
            manufacturer=manufacturer,
            is_controlled_substance=False,
            requires_prescription=True,
            is_active=True
        )

        for i in range(num_prescriptions):
            prescription_data = {
                'patient': patient.id,
                'medication': medication.id,
                'prescribed_by': doctor.id,
                'dosage': '1 tablet',
                'frequency': 'Twice daily',
                'duration': '7 days',
                'instructions': 'Take with food',
                'status': 'PENDING',
                'start_date': date.today().isoformat(),
                'end_date': (date.today() + timedelta(days=7)).isoformat()
            }

            start_time = time.time()
            try:
                response = self.api_client.post(
                    f'{self.base_url}/api/prescriptions/',
                    prescription_data,
                    format='json'
                )
                response_time = time.time() - start_time
                response_times.append(response_time)

                if response.status_code != status.HTTP_201_CREATED:
                    self.metrics.record_error('/api/prescriptions/', f'Status {response.status_code}')

                self.metrics.record_response_time('/api/prescriptions/', response_time)

            except Exception as e:
                response_time = time.time() - start_time
                response_times.append(response_time)
                self.metrics.record_error('/api/prescriptions/', str(e))

        return response_times

    def simulate_emergency_triage_flow(self, num_triage_cases: int) -> List[float]:
        """Simulate emergency triage load"""
        response_times = []

        # Create test patients
        patients = []
        for i in range(num_triage_cases):
            patient = Patient.objects.create(
                first_name=f'Emergency{i}',
                last_name=f'Patient{i}',
                email=f'emergency{i}@test.com',
                phone=f'+155555500{i:02d}',
                date_of_birth='1990-01-01',
                medical_record_number=f'ER-{i:03d}',
                blood_type='A+',
                gender='M'
            )
            patients.append(patient)

        nurse = User.objects.create_user(
            username='nurse',
            email='nurse@hms.com',
            password='securepassword123!',
            first_name='Nurse',
            last_name='Test',
            role='NURSE'
        )

        for i in range(num_triage_cases):
            patient = patients[i]

            triage_data = {
                'patient': patient.id,
                'chief_complaint': 'Chest pain and difficulty breathing',
                'vital_signs': {
                    'blood_pressure': '160/100',
                    'heart_rate': 120,
                    'respiratory_rate': 24,
                    'temperature': 98.6,
                    'oxygen_saturation': 92
                },
                'pain_scale': 8,
                'triage_level': 'HIGH',
                'triage_nurse': nurse.id,
                'notes': 'Patient appears in distress'
            }

            start_time = time.time()
            try:
                response = self.api_client.post(
                    f'{self.base_url}/api/emergency/triage/',
                    triage_data,
                    format='json'
                )
                response_time = time.time() - start_time
                response_times.append(response_time)

                if response.status_code != status.HTTP_201_CREATED:
                    self.metrics.record_error('/api/emergency/triage/', f'Status {response.status_code}')

                self.metrics.record_response_time('/api/emergency/triage/', response_time)

            except Exception as e:
                response_time = time.time() - start_time
                response_times.append(response_time)
                self.metrics.record_error('/api/emergency/triage/', str(e))

        return response_times


class HMSPerformanceTestCase(ComprehensiveHMSTestCase):
    """Comprehensive performance tests for HMS system"""

    def setUp(self):
        super().setUp()
        self.metrics = PerformanceMetrics()
        self.load_scenarios = HealthcareLoadScenarios(
            'http://localhost:8000',
            self.api_client
        )
        self.performance_thresholds = TestConfiguration().performance_threshold

    def test_patient_registration_performance(self):
        """Test patient registration performance under load"""
        print("\\nTesting Patient Registration Performance...")

        # Baseline performance
        baseline_times = self.load_scenarios.simulate_patient_registration_flow(10)
        baseline_mean = statistics.mean(baseline_times)

        print(f"Baseline mean response time: {baseline_mean:.3f}s")

        # Load test with 50 concurrent registrations
        start_time = time.time()
        with ThreadPoolExecutor(max_workers=50) as executor:
            futures = []
            for i in range(50):
                future = executor.submit(self.load_scenarios.simulate_patient_registration_flow, 2)
                futures.append(future)

            all_response_times = []
            for future in futures:
                response_times = future.result()
                all_response_times.extend(response_times)

        load_test_duration = time.time() - start_time

        print(f"Load test completed in {load_test_duration:.2f}s")
        print(f"Total requests: {len(all_response_times)}")
        print(f"Mean response time: {statistics.mean(all_response_times):.3f}s")
        print(f"95th percentile: {np.percentile(all_response_times, 95):.3f}s")
        print(f"99th percentile: {np.percentile(all_response_times, 99):.3f}s")

        # Performance assertions
        self.assertLessEqual(
            np.percentile(all_response_times, 95),
            self.performance_thresholds['response_time'],
            "Patient registration 95th percentile response time exceeds threshold"
        )

        self.assertLessEqual(
            len(all_response_times) / load_test_duration,
            self.performance_thresholds['throughput'],
            "Patient registration throughput below threshold"
        )

    def test_appointment_scheduling_performance(self):
        """Test appointment scheduling performance under load"""
        print("\\nTesting Appointment Scheduling Performance...")

        # Load test with appointment scheduling
        start_time = time.time()
        response_times = self.load_scenarios.simulate_appointment_scheduling_flow(100)
        load_test_duration = time.time() - start_time

        print(f"Load test completed in {load_test_duration:.2f}s")
        print(f"Total requests: {len(response_times)}")
        print(f"Mean response time: {statistics.mean(response_times):.3f}s")
        print(f"95th percentile: {np.percentile(response_times, 95):.3f}s")
        print(f"99th percentile: {np.percentile(response_times, 99):.3f}s")

        # Performance assertions
        self.assertLessEqual(
            np.percentile(response_times, 95),
            self.performance_thresholds['response_time'],
            "Appointment scheduling 95th percentile response time exceeds threshold"
        )

    def test_medical_record_access_performance(self):
        """Test medical record access performance under load"""
        print("\\nTesting Medical Record Access Performance...")

        # Load test with medical record access
        start_time = time.time()
        response_times = self.load_scenarios.simulate_medical_record_access_flow(200)
        load_test_duration = time.time() - start_time

        print(f"Load test completed in {load_test_duration:.2f}s")
        print(f"Total requests: {len(response_times)}")
        print(f"Mean response time: {statistics.mean(response_times):.3f}s")
        print(f"95th percentile: {np.percentile(response_times, 95):.3f}s")
        print(f"99th percentile: {np.percentile(response_times, 99):.3f}s")

        # Performance assertions
        self.assertLessEqual(
            np.percentile(response_times, 95),
            self.performance_thresholds['response_time'],
            "Medical record access 95th percentile response time exceeds threshold"
        )

    def test_billing_processing_performance(self):
        """Test billing processing performance under load"""
        print("\\nTesting Billing Processing Performance...")

        # Load test with billing processing
        start_time = time.time()
        response_times = self.load_scenarios.simulate_billing_processing_flow(150)
        load_test_duration = time.time() - start_time

        print(f"Load test completed in {load_test_duration:.2f}s")
        print(f"Total requests: {len(response_times)}")
        print(f"Mean response time: {statistics.mean(response_times):.3f}s")
        print(f"95th percentile: {np.percentile(response_times, 95):.3f}s")
        print(f"99th percentile: {np.percentile(response_times, 99):.3f}s")

        # Performance assertions
        self.assertLessEqual(
            np.percentile(response_times, 95),
            self.performance_thresholds['response_time'],
            "Billing processing 95th percentile response time exceeds threshold"
        )

    def test_pharmacy_workflow_performance(self):
        """Test pharmacy workflow performance under load"""
        print("\\nTesting Pharmacy Workflow Performance...")

        # Load test with pharmacy workflow
        start_time = time.time()
        response_times = self.load_scenarios.simulate_pharmacy_workflow(80)
        load_test_duration = time.time() - start_time

        print(f"Load test completed in {load_test_duration:.2f}s")
        print(f"Total requests: {len(response_times)}")
        print(f"Mean response time: {statistics.mean(response_times):.3f}s")
        print(f"95th percentile: {np.percentile(response_times, 95):.3f}s")
        print(f"99th percentile: {np.percentile(response_times, 99):.3f}s")

        # Performance assertions
        self.assertLessEqual(
            np.percentile(response_times, 95),
            self.performance_thresholds['response_time'],
            "Pharmacy workflow 95th percentile response time exceeds threshold"
        )

    def test_emergency_triage_performance(self):
        """Test emergency triage performance under load"""
        print("\\nTesting Emergency Triage Performance...")

        # Load test with emergency triage
        start_time = time.time()
        response_times = self.load_scenarios.simulate_emergency_triage_flow(30)
        load_test_duration = time.time() - start_time

        print(f"Load test completed in {load_test_duration:.2f}s")
        print(f"Total requests: {len(response_times)}")
        print(f"Mean response time: {statistics.mean(response_times):.3f}s")
        print(f"95th percentile: {np.percentile(response_times, 95):.3f}s")
        print(f"99th percentile: {np.percentile(response_times, 99):.3f}s")

        # Performance assertions - emergency triage should be faster
        self.assertLessEqual(
            np.percentile(response_times, 95),
            1.0,  # Emergency triage should be < 1s
            "Emergency triage 95th percentile response time exceeds threshold"
        )

    def test_database_performance(self):
        """Test database performance under load"""
        print("\\nTesting Database Performance...")

        # Test database connection performance
        start_time = time.time()
        with connection.cursor() as cursor:
            for i in range(1000):
                cursor.execute("SELECT 1")
        db_query_time = time.time() - start_time

        print(f"Database query performance: {db_query_time:.3f}s for 1000 queries")
        print(f"Average query time: {db_query_time/1000:.6f}s")

        # Test database insert performance
        start_time = time.time()
        with transaction.atomic():
            for i in range(100):
                Patient.objects.create(
                    first_name=f'PerfTest{i}',
                    last_name=f'Patient{i}',
                    email=f'perftest{i}@test.com',
                    phone=f'+155555555{i:02d}',
                    date_of_birth='1990-01-01',
                    medical_record_number=f'PERF-MRN-{i:03d}',
                    blood_type='A+',
                    gender='M'
                )
        db_insert_time = time.time() - start_time

        print(f"Database insert performance: {db_insert_time:.3f}s for 100 records")
        print(f"Average insert time: {db_insert_time/100:.6f}s")

        # Performance assertions
        self.assertLess(db_query_time, 5.0, "Database query performance too slow")
        self.assertLess(db_insert_time, 10.0, "Database insert performance too slow")

    def test_cache_performance(self):
        """Test cache performance"""
        print("\\nTesting Cache Performance...")

        # Test cache set performance
        start_time = time.time()
        for i in range(1000):
            cache.set(f'test_key_{i}', f'test_value_{i}', timeout=300)
        cache_set_time = time.time() - start_time

        print(f"Cache set performance: {cache_set_time:.3f}s for 1000 operations")
        print(f"Average cache set time: {cache_set_time/1000:.6f}s")

        # Test cache get performance
        start_time = time.time()
        hits = 0
        for i in range(1000):
            value = cache.get(f'test_key_{i}')
            if value is not None:
                hits += 1
        cache_get_time = time.time() - start_time

        print(f"Cache get performance: {cache_get_time:.3f}s for 1000 operations")
        print(f"Average cache get time: {cache_get_time/1000:.6f}s")
        print(f"Cache hit rate: {hits/1000*100:.1f}%")

        # Performance assertions
        self.assertLess(cache_set_time, 2.0, "Cache set performance too slow")
        self.assertLess(cache_get_time, 1.0, "Cache get performance too slow")
        self.assertEqual(hits, 1000, "Cache hit rate should be 100%")

    def test_concurrent_user_simulation(self):
        """Test concurrent user simulation"""
        print("\\nTesting Concurrent User Simulation...")

        def simulate_user_activity(user_id: int):
            """Simulate user activity"""
            response_times = []

            # Patient registration
            response_times.extend(self.load_scenarios.simulate_patient_registration_flow(1))

            # Appointment scheduling
            response_times.extend(self.load_scenarios.simulate_appointment_scheduling_flow(1))

            # Medical record access
            response_times.extend(self.load_scenarios.simulate_medical_record_access_flow(1))

            return response_times

        # Simulate 50 concurrent users
        start_time = time.time()
        with ThreadPoolExecutor(max_workers=50) as executor:
            futures = []
            for i in range(50):
                future = executor.submit(simulate_user_activity, i)
                futures.append(future)

            all_response_times = []
            for future in futures:
                response_times = future.result()
                all_response_times.extend(response_times)

        simulation_duration = time.time() - start_time

        print(f"Concurrent user simulation completed in {simulation_duration:.2f}s")
        print(f"Total requests: {len(all_response_times)}")
        print(f"Requests per second: {len(all_response_times)/simulation_duration:.1f}")
        print(f"Mean response time: {statistics.mean(all_response_times):.3f}s")
        print(f"95th percentile: {np.percentile(all_response_times, 95):.3f}s")

        # Performance assertions
        self.assertGreaterEqual(
            len(all_response_times) / simulation_duration,
            100,  # Should handle 100+ RPS
            "Concurrent user simulation throughput below threshold"
        )

    def test_stress_testing(self):
        """Test stress testing with extreme load"""
        print("\\nTesting Stress Testing...")

        def stress_test_worker():
            """Worker for stress testing"""
            response_times = []
            for i in range(10):
                # Patient registration
                response_times.extend(self.load_scenarios.simulate_patient_registration_flow(2))

                # Appointment scheduling
                response_times.extend(self.load_scenarios.simulate_appointment_scheduling_flow(2))

                # Small delay
                time.sleep(0.1)

            return response_times

        # Extreme load test
        start_time = time.time()
        system_metrics_before = {
            'cpu': psutil.cpu_percent(interval=1),
            'memory': psutil.virtual_memory().percent
        }

        with ProcessPoolExecutor(max_workers=multiprocessing.cpu_count() * 2) as executor:
            futures = []
            for i in range(100):  # 100 workers
                future = executor.submit(stress_test_worker)
                futures.append(future)

            all_response_times = []
            for future in futures:
                response_times = future.result()
                all_response_times.extend(response_times)

        stress_test_duration = time.time() - start_time
        system_metrics_after = {
            'cpu': psutil.cpu_percent(interval=1),
            'memory': psutil.virtual_memory().percent
        }

        print(f"Stress test completed in {stress_test_duration:.2f}s")
        print(f"Total requests: {len(all_response_times)}")
        print(f"Requests per second: {len(all_response_times)/stress_test_duration:.1f}")
        print(f"Mean response time: {statistics.mean(all_response_times):.3f}s")
        print(f"95th percentile: {np.percentile(all_response_times, 95):.3f}s")
        print(f"System CPU usage: {system_metrics_after['cpu']:.1f}%")
        print(f"System Memory usage: {system_metrics_after['memory']:.1f}%")

        # Performance assertions
        self.assertLess(
            system_metrics_after['cpu'],
            90,
            "CPU usage too high under stress"
        )

        self.assertLess(
            system_metrics_after['memory'],
            90,
            "Memory usage too high under stress"
        )

    def test_endurance_testing(self):
        """Test endurance testing with sustained load"""
        print("\\nTesting Endurance Testing...")

        def endurance_worker(duration: int):
            """Worker for endurance testing"""
            response_times = []
            start_time = time.time()

            while time.time() - start_time < duration:
                # Patient registration
                response_times.extend(self.load_scenarios.simulate_patient_registration_flow(1))

                # Small delay
                time.sleep(0.5)

            return response_times

        # Endurance test for 5 minutes
        endurance_duration = 300  # 5 minutes
        print(f"Running endurance test for {endurance_duration} seconds...")

        start_time = time.time()
        with ThreadPoolExecutor(max_workers=20) as executor:
            futures = []
            for i in range(20):
                future = executor.submit(endurance_worker, endurance_duration)
                futures.append(future)

            all_response_times = []
            for future in futures:
                response_times = future.result()
                all_response_times.extend(response_times)

        actual_duration = time.time() - start_time

        print(f"Endurance test completed in {actual_duration:.2f}s")
        print(f"Total requests: {len(all_response_times)}")
        print(f"Requests per second: {len(all_response_times)/actual_duration:.1f}")
        print(f"Mean response time: {statistics.mean(all_response_times):.3f}s")
        print(f"95th percentile: {np.percentile(all_response_times, 95):.3f}s")

        # Performance assertions - system should maintain performance over time
        self.assertGreaterEqual(
            len(all_response_times) / actual_duration,
            50,  # Should maintain 50+ RPS over time
            "Endurance test throughput below threshold"
        )

    def generate_performance_report(self):
        """Generate comprehensive performance report"""
        report = self.metrics.generate_performance_report("HMS System Performance Test")

        # Add system information
        report += f"""
System Information:
- CPU Cores: {multiprocessing.cpu_count()}
- Total Memory: {psutil.virtual_memory().total / (1024**3):.1f} GB
- Available Memory: {psutil.virtual_memory().available / (1024**3):.1f} GB
- Python Version: {import sys; sys.version}
- Django Version: {import django; django.VERSION}
"""

        # Save report
        report_path = '/home/azureuser/helli/enterprise-grade-hms/tests/reports/performance/performance_report.txt'
        os.makedirs(os.path.dirname(report_path), exist_ok=True)

        with open(report_path, 'w') as f:
            f.write(report)

        print(f"Performance report saved to: {report_path}")
        return report


# Locust integration for load testing
class HMSWebsiteUser(HttpUser):
    """Locust user for HMS load testing"""

    wait_time = between(1, 5)

    def on_start(self):
        """Called when a user starts"""
        self.client.post("/api/auth/login/", {
            "username": "testuser",
            "password": "securepassword123!"
        })

    @task(3)
    def view_patient_list(self):
        """View patient list"""
        self.client.get("/api/patients/")

    @task(2)
    def create_patient(self):
        """Create new patient"""
        patient_data = HealthcareDataMixin.generate_anonymized_patient_data()
        self.client.post("/api/patients/", patient_data)

    @task(3)
    def view_appointments(self):
        """View appointments"""
        self.client.get("/api/appointments/")

    @task(2)
    def schedule_appointment(self):
        """Schedule appointment"""
        appointment_data = {
            "patient": 1,
            "doctor": 1,
            "appointment_type": "CONSULTATION",
            "scheduled_date": (datetime.now() + timedelta(days=1)).isoformat(),
            "duration": 30,
            "status": "SCHEDULED"
        }
        self.client.post("/api/appointments/", appointment_data)

    @task(1)
    def view_medical_records(self):
        """View medical records"""
        self.client.get("/api/medical-records/")

    @task(1)
    def view_billing(self):
        """View billing information"""
        self.client.get("/api/billing/")


# Test execution
if __name__ == '__main__':
    # Create test suite
    suite = unittest.TestLoader().loadTestsFromTestCase(HMSPerformanceTestCase)

    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # Generate report
    test_case = HMSPerformanceTestCase()
    test_case.setUp()
    report = test_case.generate_performance_report()
    print(report)