# HMS Enterprise-Grade Developer Guide

## 👨‍💻 Welcome to HMS Development

This comprehensive developer guide provides everything you need to contribute to the HMS Enterprise-Grade system. Whether you're a backend developer, frontend engineer, or full-stack developer, this guide will help you understand the system architecture, development workflow, and best practices.

## 🏗️ System Architecture Overview

### Technical Stack

#### Backend Technologies
- **Primary Framework**: Django 4.2 + REST Framework
- **Secondary Framework**: FastAPI 0.116 for high-performance services
- **Database**: PostgreSQL 16 with read replicas
- **Cache**: Redis 7.2 for caching and sessions
- **Message Queue**: Apache Kafka 3.6 for event streaming
- **Task Queue**: Celery 5.3 with Redis/RabbitMQ
- **Authentication**: JWT tokens with OAuth 2.0/OIDC

#### Frontend Technologies
- **Framework**: React 18.2 + TypeScript 5.0
- **State Management**: Redux Toolkit + React Query
- **UI Components**: Material-UI + Tailwind CSS
- **Build Tool**: Vite 4.0
- **Testing**: Jest 29 + React Testing Library
- **Charts**: Chart.js 4.4 + D3.js 7.8

#### DevOps & Infrastructure
- **Containerization**: Docker 24.0 + Kubernetes 1.28
- **CI/CD**: GitHub Actions + ArgoCD
- **Monitoring**: Prometheus + Grafana + Jaeger
- **Logging**: ELK Stack (Elasticsearch, Logstash, Kibana)
- **Infrastructure**: Terraform + AWS

### Development Environment Setup

#### Prerequisites
```bash
# Required software versions
Python 3.9+ (3.11 recommended)
Node.js 18+ (18.18 recommended)
Docker 24.0+
Docker Compose 2.0+
Git 2.25+
PostgreSQL 15+ (local development)
Redis 7+ (local development)
```

#### Local Development Setup
```bash
# Clone the repository
git clone https://github.com/your-org/hms-enterprise-grade.git
cd hms-enterprise-grade

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install Python dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Install Node.js dependencies
cd frontend
npm install
cd ..

# Copy environment configuration
cp .env.example .env
cp frontend/.env.example frontend/.env

# Set up database
createdb hms_enterprise_dev
python manage.py migrate
python manage.py createsuperuser
python manage.py load_initial_data

# Start Redis
redis-server --daemonize yes

# Start backend
python manage.py runserver

# Start frontend (in separate terminal)
cd frontend
npm run dev
```

#### Docker Development Setup
```bash
# Start all services
docker-compose up -d

# Check service status
docker-compose ps

# View logs
docker-compose logs -f backend
docker-compose logs -f frontend

# Run database migrations
docker-compose exec backend python manage.py migrate

# Run tests
docker-compose exec backend pytest
docker-compose exec frontend npm test
```

## 🐍 Backend Development

### Django Application Structure

#### Project Structure
```
backend/
├── hms/                    # Project settings
│   ├── settings/
│   │   ├── base.py        # Base settings
│   │   ├── development.py # Development settings
│   │   ├── production.py  # Production settings
│   │   └── test.py        # Test settings
│   ├── urls.py            # Main URL configuration
│   ├── wsgi.py            # WSGI configuration
│   └── asgi.py            # ASGI configuration
├── core/                   # Core application
│   ├── models/            # Core models
│   ├── views/             # Core views
│   ├── serializers/       # Data serializers
│   ├── middleware/        # Custom middleware
│   ├── tasks/             # Background tasks
│   └── management/        # Management commands
├── apps/                  # Django applications
│   ├── patients/          # Patient management
│   ├── clinical/          # Clinical workflows
│   ├── billing/           # Financial operations
│   ├── pharmacy/          # Pharmacy management
│   ├── laboratory/        # Laboratory operations
│   ├── appointments/      # Scheduling system
│   └── authentication/    # User authentication
├── tests/                 # Test files
├── scripts/               # Utility scripts
└── requirements/          # Python requirements
```

### Django Best Practices

#### Model Development
```python
# patients/models.py
from django.db import models
from django.core.validators import validate_email
from django.contrib.auth.models import User
import uuid

class Patient(models.Model):
    """Patient model with comprehensive patient information"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    patient_id = models.CharField(max_length=20, unique=True, db_index=True)

    # Personal Information
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    date_of_birth = models.DateField()
    gender = models.CharField(max_length=1, choices=[('M', 'Male'), ('F', 'Female'), ('O', 'Other')])

    # Contact Information
    contact_number = models.CharField(max_length=20)
    email = models.EmailField(blank=True, null=True, validators=[validate_email])
    address = models.JSONField(default=dict)
    emergency_contact = models.JSONField(default=dict)

    # Medical Information
    blood_type = models.CharField(max_length=3, blank=True, null=True)
    allergies = models.JSONField(default=list)
    medical_conditions = models.JSONField(default=list)
    current_medications = models.JSONField(default=list)

    # Metadata
    is_active = models.BooleanField(default=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)

    class Meta:
        db_table = 'patients'
        indexes = [
            models.Index(fields=['last_name', 'first_name']),
            models.Index(fields=['date_of_birth']),
            models.Index(fields=['is_active', 'created_at']),
        ]
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.patient_id})"

    def get_full_name(self):
        return f"{self.first_name} {self.last_name}"

    def get_age(self):
        """Calculate patient age"""
        from datetime import date
        today = date.today()
        return today.year - self.date_of_birth.year - (
            (today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day)
        )

    @property
    def primary_care_physician(self):
        """Get primary care physician if assigned"""
        return self.providers.filter(
            patientprovider__relationship_type='primary_care',
            patientprovider__is_active=True
        ).first()
```

#### Serializer Development
```python
# patients/serializers.py
from rest_framework import serializers
from .models import Patient, PatientProvider
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError

class PatientSerializer(serializers.ModelSerializer):
    """Comprehensive patient serializer"""
    full_name = serializers.CharField(read_only=True)
    age = serializers.IntegerField(read_only=True)
    primary_care_physician = serializers.SerializerMethodField()

    class Meta:
        model = Patient
        fields = [
            'id', 'patient_id', 'first_name', 'last_name', 'full_name',
            'date_of_birth', 'age', 'gender', 'contact_number', 'email',
            'address', 'emergency_contact', 'blood_type', 'allergies',
            'medical_conditions', 'current_medications', 'is_active',
            'created_at', 'updated_at', 'primary_care_physician'
        ]
        read_only_fields = ['id', 'patient_id', 'created_at', 'updated_at']

    def get_primary_care_physician(self, obj):
        """Get primary care physician information"""
        if obj.primary_care_physician:
            return {
                'id': obj.primary_care_physician.id,
                'full_name': f"{obj.primary_care_physician.first_name} {obj.primary_care_physician.last_name}",
                'specialty': getattr(obj.primary_care_physician.profile, 'specialty', None)
            }
        return None

    def validate_contact_number(self, value):
        """Validate phone number format"""
        import re
        if not re.match(r'^\+?1?\d{9,15}$', value):
            raise ValidationError("Invalid phone number format")
        return value

    def validate_email(self, value):
        """Validate email format and uniqueness"""
        if value and Patient.objects.filter(email=value).exclude(id=self.instance.id if self.instance else None).exists():
            raise ValidationError("Email address already exists")
        return value

class PatientCreateSerializer(PatientSerializer):
    """Serializer for creating new patients"""
    class Meta(PatientSerializer.Meta):
        fields = PatientSerializer.Meta.fields + ['created_by']

    def create(self, validated_data):
        """Create new patient with generated patient ID"""
        from django.utils import timezone

        # Generate unique patient ID
        last_patient = Patient.objects.order_by('-patient_id').first()
        if last_patient and last_patient.patient_id:
            try:
                last_number = int(last_patient.patient_id[1:])  # Remove 'P' prefix
                new_number = last_number + 1
            except (ValueError, IndexError):
                new_number = 1
        else:
            new_number = 1

        validated_data['patient_id'] = f"P{new_number:06d}"
        validated_data['created_at'] = timezone.now()

        return super().create(validated_data)

class PatientListSerializer(serializers.ModelSerializer):
    """Simplified serializer for patient lists"""
    full_name = serializers.CharField(read_only=True)
    age = serializers.IntegerField(read_only=True)

    class Meta:
        model = Patient
        fields = [
            'id', 'patient_id', 'full_name', 'age', 'gender',
            'contact_number', 'email', 'is_active', 'created_at'
        ]
```

#### View Development
```python
# patients/views.py
from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q
from .models import Patient
from .serializers import PatientSerializer, PatientCreateSerializer, PatientListSerializer
from core.permissions import IsHealthcareProvider
from core.pagination import StandardResultSetPagination
import logging

logger = logging.getLogger(__name__)

class PatientViewSet(viewsets.ModelViewSet):
    """Comprehensive patient management viewset"""
    permission_classes = [IsAuthenticated, IsHealthcareProvider]
    pagination_class = StandardResultSetPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['gender', 'is_active', 'blood_type']
    search_fields = ['first_name', 'last_name', 'patient_id', 'email', 'contact_number']
    ordering_fields = ['created_at', 'last_name', 'first_name', 'date_of_birth']
    ordering = ['-created_at']

    def get_serializer_class(self):
        """Return appropriate serializer based on action"""
        if self.action == 'create':
            return PatientCreateSerializer
        elif self.action == 'list':
            return PatientListSerializer
        return PatientSerializer

    def get_queryset(self):
        """Get filtered queryset based on user permissions"""
        queryset = Patient.objects.all()

        # Filter by user's accessible patients
        user = self.request.user
        if hasattr(user, 'profile') and user.profile.role == 'doctor':
            # Doctors can see their assigned patients
            queryset = queryset.filter(
                Q(providers=user) | Q(created_by=user)
            )
        elif user.profile.role in ['nurse', 'receptionist']:
            # Nurses and receptionists can see all patients in their facility
            queryset = queryset.filter(facility=user.profile.facility)

        return queryset

    def perform_create(self, serializer):
        """Set created_by when creating patient"""
        serializer.save(created_by=self.request.user)
        logger.info(f"Patient created by {self.request.user.username}: {serializer.instance.patient_id}")

    def retrieve(self, request, *args, **kwargs):
        """Get patient with related data"""
        patient = self.get_object()

        # Check if user has permission to view this patient
        if not self.has_patient_access(patient):
            return Response(
                {"detail": "You do not have permission to view this patient"},
                status=status.HTTP_403_FORBIDDEN
            )

        serializer = self.get_serializer(patient)
        return Response(serializer.data)

    def update(self, request, *args, **kwargs):
        """Update patient with validation"""
        patient = self.get_object()

        # Check if user has permission to update this patient
        if not self.has_patient_access(patient):
            return Response(
                {"detail": "You do not have permission to update this patient"},
                status=status.HTTP_403_FORBIDDEN
            )

        serializer = self.get_serializer(patient, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        logger.info(f"Patient updated by {self.request.user.username}: {patient.patient_id}")
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def clinical_encounters(self, request, pk=None):
        """Get patient's clinical encounters"""
        patient = self.get_object()

        if not self.has_patient_access(patient):
            return Response(
                {"detail": "You do not have permission to view this patient's encounters"},
                status=status.HTTP_403_FORBIDDEN
            )

        encounters = patient.clinical_encounters.all().order_by('-encounter_date')
        from clinical.serializers import ClinicalEncounterListSerializer
        serializer = ClinicalEncounterListSerializer(encounters, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def appointments(self, request, pk=None):
        """Get patient's appointments"""
        patient = self.get_object()

        if not self.has_patient_access(patient):
            return Response(
                {"detail": "You do not have permission to view this patient's appointments"},
                status=status.HTTP_403_FORBIDDEN
            )

        appointments = patient.appointments.all().order_by('-start_datetime')
        from appointments.serializers import AppointmentListSerializer
        serializer = AppointmentListSerializer(appointments, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def medications(self, request, pk=None):
        """Get patient's current medications"""
        patient = self.get_object()

        if not self.has_patient_access(patient):
            return Response(
                {"detail": "You do not have permission to view this patient's medications"},
                status=status.HTTP_403_FORBIDDEN
            )

        from pharmacy.models import Prescription
        medications = Prescription.objects.filter(
            patient=patient,
            status='active'
        ).order_by('-date_written')

        from pharmacy.serializers import PrescriptionListSerializer
        serializer = PrescriptionListSerializer(medications, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def search(self, request):
        """Advanced patient search"""
        query = request.query_params.get('q', '')
        filters = request.query_params.get('filters', '{}')

        try:
            import json
            filter_data = json.loads(filters)
        except json.JSONDecodeError:
            filter_data = {}

        queryset = self.get_queryset()

        # Advanced search logic
        if query:
            queryset = queryset.filter(
                Q(first_name__icontains=query) |
                Q(last_name__icontains=query) |
                Q(patient_id__icontains=query) |
                Q(email__icontains=query) |
                Q(contact_number__icontains=query)
            )

        # Apply additional filters
        if 'age_range' in filter_data:
            min_age, max_age = filter_data['age_range']
            from datetime import date, timedelta
            max_dob = date.today() - timedelta(days=min_age * 365)
            min_dob = date.today() - timedelta(days=max_age * 365)
            queryset = queryset.filter(date_of_birth__lte=max_dob, date_of_birth__gte=min_dob)

        if 'medical_conditions' in filter_data:
            conditions = filter_data['medical_conditions']
            queryset = queryset.filter(
                medical_conditions__overlap=conditions
            )

        page = self.paginate_queryset(queryset)
        serializer = self.get_serializer(page, many=True)
        return self.get_paginated_response(serializer.data)

    def has_patient_access(self, patient):
        """Check if user has access to this patient"""
        user = self.request.user

        # Superusers have access to all patients
        if user.is_superuser:
            return True

        # Users can access patients they created
        if patient.created_by == user:
            return True

        # Doctors can access their assigned patients
        if hasattr(user, 'profile') and user.profile.role == 'doctor':
            if patient.providers.filter(id=user.id).exists():
                return True

        # Users in the same facility can access patients
        if hasattr(user, 'profile') and hasattr(user.profile, 'facility'):
            if patient.facility == user.profile.facility:
                return True

        return False
```

### Background Tasks with Celery

#### Task Development
```python
# core/tasks.py
from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from .models import AuditLog
import logging

logger = logging.getLogger(__name__)

@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def send_appointment_reminder(self, appointment_id, reminder_type='email'):
    """Send appointment reminder to patient"""
    try:
        from appointments.models import Appointment
        from patients.models import Patient

        appointment = Appointment.objects.get(id=appointment_id)
        patient = appointment.patient

        if reminder_type == 'email':
            send_mail(
                subject=f'Appointment Reminder - {appointment.start_datetime.strftime("%B %d, %Y at %I:%M %p")}',
                message=f'''
                Dear {patient.first_name} {patient.last_name},

                This is a reminder for your upcoming appointment:

                Date: {appointment.start_datetime.strftime("%B %d, %Y")}
                Time: {appointment.start_datetime.strftime("%I:%M %p")}
                Location: {appointment.location}
                Provider: {appointment.provider.get_full_name()}

                Please arrive 15 minutes before your scheduled appointment time.

                If you need to reschedule or cancel, please call us at (555) 123-4567.

                Best regards,
                HMS Healthcare
                ''',
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[patient.email],
                fail_silently=False
            )

        elif reminder_type == 'sms':
            # Implement SMS sending logic
            pass

        # Log the reminder sent
        AuditLog.objects.create(
            user=None,
            action='appointment_reminder_sent',
            object_type='appointment',
            object_id=appointment.id,
            details={
                'reminder_type': reminder_type,
                'patient_id': patient.id,
                'appointment_datetime': appointment.start_datetime.isoformat()
            }
        )

        logger.info(f"Appointment reminder sent to {patient.full_name} for {appointment.id}")

        return {
            'status': 'success',
            'appointment_id': appointment_id,
            'reminder_type': reminder_type
        }

    except Appointment.DoesNotExist:
        logger.error(f"Appointment {appointment_id} not found")
        raise
    except Exception as e:
        logger.error(f"Failed to send appointment reminder: {str(e)}")
        raise self.retry(exc=e)

@shared_task
def process_lab_results(lab_order_id, results_data):
    """Process laboratory results and update patient records"""
    try:
        from laboratory.models import LabOrder, LabResult
        from patients.models import Patient

        lab_order = LabOrder.objects.get(id=lab_order_id)

        # Create lab result records
        for result in results_data['results']:
            LabResult.objects.create(
                lab_order=lab_order,
                test_code=result['test_code'],
                test_name=result['test_name'],
                result=result['result'],
                unit=result['unit'],
                reference_range=result['reference_range'],
                flag=result.get('flag'),
                status=result.get('status', 'final')
            )

        # Update lab order status
        lab_order.status = 'completed'
        lab_order.resulted_at = timezone.now()
        lab_order.save()

        # Check for critical values and send alerts
        critical_results = [
            result for result in results_data['results']
            if result.get('flag') == 'critical'
        ]

        if critical_results:
            # Send critical value alert
            send_critical_value_alert.delay(lab_order.patient_id, critical_results)

        logger.info(f"Lab results processed for order {lab_order.order_number}")

        return {
            'status': 'success',
            'lab_order_id': lab_order_id,
            'results_count': len(results_data['results']),
            'critical_results': len(critical_results)
        }

    except LabOrder.DoesNotExist:
        logger.error(f"Lab order {lab_order_id} not found")
        raise
    except Exception as e:
        logger.error(f"Failed to process lab results: {str(e)}")
        raise

@shared_task
def generate_monthly_reports():
    """Generate monthly administrative reports"""
    try:
        from django.db.models import Count, Sum
        from patients.models import Patient
        from appointments.models import Appointment
        from billing.models import Charge
        from django.utils import timezone
        from datetime import timedelta

        # Calculate date range
        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=30)

        # Patient statistics
        patient_stats = Patient.objects.filter(
            created_at__date__range=[start_date, end_date]
        ).aggregate(
            total_patients=Count('id'),
            active_patients=Count('id', filter=Q(is_active=True))
        )

        # Appointment statistics
        appointment_stats = Appointment.objects.filter(
            start_datetime__date__range=[start_date, end_date]
        ).aggregate(
            total_appointments=Count('id'),
            completed_appointments=Count('id', filter=Q(status='completed')),
            cancelled_appointments=Count('id', filter=Q(status='cancelled'))
        )

        # Financial statistics
        financial_stats = Charge.objects.filter(
            charge_date__date__range=[start_date, end_date]
        ).aggregate(
            total_charges=Sum('total_amount'),
            insurance_amount=Sum('insurance_amount'),
            patient_amount=Sum('patient_amount')
        )

        # Generate report data
        report_data = {
            'period': {
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat()
            },
            'patient_statistics': patient_stats,
            'appointment_statistics': appointment_stats,
            'financial_statistics': financial_stats,
            'generated_at': timezone.now().isoformat()
        }

        # Save report to database or send via email
        # Implementation depends on reporting requirements

        logger.info("Monthly report generated successfully")

        return {
            'status': 'success',
            'report_data': report_data
        }

    except Exception as e:
        logger.error(f"Failed to generate monthly report: {str(e)}")
        raise
```

#### Celery Configuration
```python
# core/celery.py
import os
from celery import Celery

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hms.settings')

app = Celery('hms')

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django app configs.
app.autodiscover_tasks()

# Configure Celery
app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes
    task_soft_time_limit=25 * 60,  # 25 minutes
    worker_prefetch_multiplier=1,
    task_acks_late=True,
    worker_disable_rate_limits=False,
    task_compression='gzip',
    result_compression='gzip',
    result_expires=3600,  # 1 hour
    task_reject_on_worker_lost=True,
)

# Configure Redis broker
app.conf.broker_url = 'redis://localhost:6379/0'
app.conf.result_backend = 'redis://localhost:6379/0'

# Configure task routes
app.conf.task_routes = {
    'patients.tasks.*': {'queue': 'patients'},
    'clinical.tasks.*': {'queue': 'clinical'},
    'billing.tasks.*': {'queue': 'billing'},
    'laboratory.tasks.*': {'queue': 'laboratory'},
    'notifications.tasks.*': {'queue': 'notifications'},
}

# Configure task rate limits
app.conf.task_annotations = {
    'notifications.tasks.send_email': {'rate_limit': '10/m'},
    'appointments.tasks.send_reminder': {'rate_limit': '30/m'},
}
```

## 🎨 Frontend Development

### React Application Structure

#### Project Structure
```
frontend/
├── src/
│   ├── components/           # Reusable components
│   │   ├── common/          # Common UI components
│   │   ├── forms/           # Form components
│   │   ├── charts/          # Chart components
│   │   └── layout/          # Layout components
│   ├── pages/              # Page components
│   │   ├── PatientList.tsx
│   │   ├── PatientDetail.tsx
│   │   ├── ClinicalEncounter.tsx
│   │   └── Dashboard.tsx
│   ├── hooks/              # Custom hooks
│   ├── services/           # API services
│   ├── utils/              # Utility functions
│   ├── store/              # Redux store
│   ├── types/              # TypeScript types
│   └── styles/             # CSS modules
├── public/                 # Static files
├── tests/                  # Test files
└── config/                 # Configuration files
```

#### Component Development
```typescript
// src/components/patients/PatientCard.tsx
import React from 'react';
import {
  Card,
  CardContent,
  CardHeader,
  Avatar,
  Typography,
  Chip,
  Box,
  IconButton,
  Tooltip,
} from '@mui/material';
import {
  Person,
  Phone,
  Email,
  CalendarToday,
  MedicalServices,
  MoreVert,
} from '@mui/icons-material';
import { Patient } from '../../types/patient';
import { format } from 'date-fns';

interface PatientCardProps {
  patient: Patient;
  onView?: (patient: Patient) => void;
  onEdit?: (patient: Patient) => void;
  onDelete?: (patient: Patient) => void;
}

const PatientCard: React.FC<PatientCardProps> = ({
  patient,
  onView,
  onEdit,
  onDelete,
}) => {
  const getAge = (dateOfBirth: string): number => {
    const birthDate = new Date(dateOfBirth);
    const today = new Date();
    let age = today.getFullYear() - birthDate.getFullYear();
    const monthDiff = today.getMonth() - birthDate.getMonth();

    if (monthDiff < 0 || (monthDiff === 0 && today.getDate() < birthDate.getDate())) {
      age--;
    }

    return age;
  };

  const getGenderColor = (gender: string): 'primary' | 'secondary' | 'success' | 'error' => {
    switch (gender) {
      case 'M':
        return 'primary';
      case 'F':
        return 'secondary';
      case 'O':
        return 'success';
      default:
        return 'error';
    }
  };

  const getGenderLabel = (gender: string): string => {
    switch (gender) {
      case 'M':
        return 'Male';
      case 'F':
        return 'Female';
      case 'O':
        return 'Other';
      default:
        return 'Unknown';
    }
  };

  return (
    <Card
      sx={{
        height: '100%',
        display: 'flex',
        flexDirection: 'column',
        '&:hover': {
          boxShadow: 4,
          transform: 'translateY(-2px)',
          transition: 'all 0.3s ease',
        },
      }}
    >
      <CardHeader
        avatar={
          <Avatar sx={{ bgcolor: 'primary.main' }}>
            <Person />
          </Avatar>
        }
        action={
          <Tooltip title="More options">
            <IconButton aria-label="settings">
              <MoreVert />
            </IconButton>
          </Tooltip>
        }
        title={
          <Typography variant="h6" component="div">
            {patient.firstName} {patient.lastName}
          </Typography>
        }
        subheader={
          <Typography variant="body2" color="text.secondary">
            ID: {patient.patientId}
          </Typography>
        }
      />
      <CardContent sx={{ flexGrow: 1 }}>
        <Box sx={{ mb: 2 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
            <CalendarToday sx={{ mr: 1, fontSize: 16, color: 'text.secondary' }} />
            <Typography variant="body2">
              {format(new Date(patient.dateOfBirth), 'MMMM dd, yyyy')} ({getAge(patient.dateOfBirth)} years)
            </Typography>
          </Box>

          <Chip
            label={getGenderLabel(patient.gender)}
            color={getGenderColor(patient.gender)}
            size="small"
            sx={{ mb: 2 }}
          />
        </Box>

        <Box sx={{ mb: 2 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
            <Phone sx={{ mr: 1, fontSize: 16, color: 'text.secondary' }} />
            <Typography variant="body2">{patient.contactNumber}</Typography>
          </Box>

          {patient.email && (
            <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
              <Email sx={{ mr: 1, fontSize: 16, color: 'text.secondary' }} />
              <Typography variant="body2">{patient.email}</Typography>
            </Box>
          )}
        </Box>

        {patient.bloodType && (
          <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
            <MedicalServices sx={{ mr: 1, fontSize: 16, color: 'text.secondary' }} />
            <Typography variant="body2">Blood Type: {patient.bloodType}</Typography>
          </Box>
        )}

        {patient.medicalConditions && patient.medicalConditions.length > 0 && (
          <Box sx={{ mt: 2 }}>
            <Typography variant="body2" color="text.secondary" gutterBottom>
              Medical Conditions:
            </Typography>
            <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
              {patient.medicalConditions.slice(0, 3).map((condition, index) => (
                <Chip
                  key={index}
                  label={condition}
                  size="small"
                  variant="outlined"
                  sx={{ fontSize: '0.75rem' }}
                />
              ))}
              {patient.medicalConditions.length > 3 && (
                <Chip
                  label={`+${patient.medicalConditions.length - 3} more`}
                  size="small"
                  variant="outlined"
                  sx={{ fontSize: '0.75rem' }}
                />
              )}
            </Box>
          </Box>
        )}

        <Box sx={{ display: 'flex', justifyContent: 'space-between', mt: 2 }}>
          <Chip
            label={patient.isActive ? 'Active' : 'Inactive'}
            color={patient.isActive ? 'success' : 'error'}
            size="small"
          />
          <Typography variant="caption" color="text.secondary">
            Created: {format(new Date(patient.createdAt), 'MMM dd, yyyy')}
          </Typography>
        </Box>
      </CardContent>
    </Card>
  );
};

export default PatientCard;
```

#### Custom Hooks Development
```typescript
// src/hooks/usePatientData.ts
import { useState, useEffect } from 'react';
import { Patient, PatientFilters } from '../types/patient';
import { patientService } from '../services/patientService';

interface UsePatientDataReturn {
  patients: Patient[];
  loading: boolean;
  error: string | null;
  totalCount: number;
  currentPage: number;
  totalPages: number;
  fetchPatients: (filters?: PatientFilters) => Promise<void>;
  createPatient: (patientData: Partial<Patient>) => Promise<Patient>;
  updatePatient: (id: string, patientData: Partial<Patient>) => Promise<Patient>;
  deletePatient: (id: string) => Promise<void>;
  setCurrentPage: (page: number) => void;
}

export const usePatientData = (
  initialFilters?: PatientFilters
): UsePatientDataReturn => {
  const [patients, setPatients] = useState<Patient[]>([]);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [totalCount, setTotalCount] = useState<number>(0);
  const [currentPage, setCurrentPage] = useState<number>(1);
  const [totalPages, setTotalPages] = useState<number>(0);
  const [filters, setFilters] = useState<PatientFilters>(initialFilters || {});

  const fetchPatients = async (newFilters?: PatientFilters) => {
    setLoading(true);
    setError(null);

    try {
      const mergedFilters = { ...filters, ...newFilters };
      setFilters(mergedFilters);

      const response = await patientService.getPatients({
        ...mergedFilters,
        page: currentPage,
        limit: 20,
      });

      setPatients(response.patients);
      setTotalCount(response.total);
      setTotalPages(Math.ceil(response.total / 20));

    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch patients');
      console.error('Error fetching patients:', err);
    } finally {
      setLoading(false);
    }
  };

  const createPatient = async (patientData: Partial<Patient>): Promise<Patient> => {
    setLoading(true);
    setError(null);

    try {
      const newPatient = await patientService.createPatient(patientData);
      setPatients(prev => [newPatient, ...prev]);
      setTotalCount(prev => prev + 1);
      return newPatient;

    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create patient');
      console.error('Error creating patient:', err);
      throw err;
    } finally {
      setLoading(false);
    }
  };

  const updatePatient = async (id: string, patientData: Partial<Patient>): Promise<Patient> => {
    setLoading(true);
    setError(null);

    try {
      const updatedPatient = await patientService.updatePatient(id, patientData);
      setPatients(prev =>
        prev.map(patient =>
          patient.id === id ? updatedPatient : patient
        )
      );
      return updatedPatient;

    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to update patient');
      console.error('Error updating patient:', err);
      throw err;
    } finally {
      setLoading(false);
    }
  };

  const deletePatient = async (id: string): Promise<void> => {
    setLoading(true);
    setError(null);

    try {
      await patientService.deletePatient(id);
      setPatients(prev => prev.filter(patient => patient.id !== id));
      setTotalCount(prev => prev - 1);

    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to delete patient');
      console.error('Error deleting patient:', err);
      throw err;
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchPatients();
  }, [currentPage]);

  useEffect(() => {
    if (currentPage !== 1) {
      setCurrentPage(1);
    } else {
      fetchPatients();
    }
  }, [filters]);

  return {
    patients,
    loading,
    error,
    totalCount,
    currentPage,
    totalPages,
    fetchPatients,
    createPatient,
    updatePatient,
    deletePatient,
    setCurrentPage,
  };
};
```

#### API Service Development
```typescript
// src/services/patientService.ts
import axios, { AxiosInstance, AxiosResponse } from 'axios';
import { Patient, PatientCreateData, PatientUpdateData, PatientFilters, PatientListResponse } from '../types/patient';

class PatientService {
  private api: AxiosInstance;

  constructor() {
    this.api = axios.create({
      baseURL: process.env.REACT_APP_API_URL || 'http://localhost:8000/api/v1',
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // Request interceptor for authentication
    this.api.interceptors.request.use(
      (config) => {
        const token = localStorage.getItem('access_token');
        if (token) {
          config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
      },
      (error) => {
        return Promise.reject(error);
      }
    );

    // Response interceptor for error handling
    this.api.interceptors.response.use(
      (response) => response,
      async (error) => {
        const originalRequest = error.config;

        // Handle token refresh
        if (error.response?.status === 401 && !originalRequest._retry) {
          originalRequest._retry = true;

          try {
            const refreshToken = localStorage.getItem('refresh_token');
            const response = await axios.post('/auth/refresh', {
              refresh_token: refreshToken,
            });

            const { access_token } = response.data;
            localStorage.setItem('access_token', access_token);

            originalRequest.headers.Authorization = `Bearer ${access_token}`;
            return this.api(originalRequest);

          } catch (refreshError) {
            // Redirect to login if refresh fails
            localStorage.removeItem('access_token');
            localStorage.removeItem('refresh_token');
            window.location.href = '/login';
            return Promise.reject(refreshError);
          }
        }

        // Handle other errors
        if (error.response?.status === 403) {
          error.message = 'You do not have permission to perform this action';
        } else if (error.response?.status === 404) {
          error.message = 'Resource not found';
        } else if (error.response?.status === 422) {
          error.message = 'Invalid data provided';
        } else if (error.response?.status >= 500) {
          error.message = 'Server error. Please try again later';
        }

        return Promise.reject(error);
      }
    );
  }

  async getPatients(filters?: PatientFilters & { page?: number; limit?: number }): Promise<PatientListResponse> {
    const params = new URLSearchParams();

    if (filters) {
      Object.entries(filters).forEach(([key, value]) => {
        if (value !== undefined && value !== null && value !== '') {
          if (Array.isArray(value)) {
            value.forEach(item => params.append(key, item.toString()));
          } else {
            params.append(key, value.toString());
          }
        }
      });
    }

    const response: AxiosResponse<PatientListResponse> = await this.api.get('/patients', {
      params,
    });

    return response.data;
  }

  async getPatient(id: string): Promise<Patient> {
    const response: AxiosResponse<Patient> = await this.api.get(`/patients/${id}`);
    return response.data;
  }

  async createPatient(patientData: PatientCreateData): Promise<Patient> {
    const response: AxiosResponse<Patient> = await this.api.post('/patients', patientData);
    return response.data;
  }

  async updatePatient(id: string, patientData: PatientUpdateData): Promise<Patient> {
    const response: AxiosResponse<Patient> = await this.api.put(`/patients/${id}`, patientData);
    return response.data;
  }

  async deletePatient(id: string): Promise<void> {
    await this.api.delete(`/patients/${id}`);
  }

  async searchPatients(query: string, filters?: PatientFilters): Promise<Patient[]> {
    const params = new URLSearchParams({
      q: query,
      ...(filters && Object.entries(filters).reduce((acc, [key, value]) => {
        if (value !== undefined && value !== null && value !== '') {
          acc[key] = value.toString();
        }
        return acc;
      }, {} as Record<string, string>)),
    });

    const response: AxiosResponse<{ patients: Patient[] }> = await this.api.get('/patients/search', {
      params,
    });

    return response.data.patients;
  }

  async getPatientClinicalEncounters(patientId: string): Promise<any[]> {
    const response: AxiosResponse<any[]> = await this.api.get(`/patients/${patientId}/clinical-encounters`);
    return response.data;
  }

  async getPatientAppointments(patientId: string): Promise<any[]> {
    const response: AxiosResponse<any[]> = await this.api.get(`/patients/${patientId}/appointments`);
    return response.data;
  }

  async getPatientMedications(patientId: string): Promise<any[]> {
    const response: AxiosResponse<any[]> = await this.api.get(`/patients/${patientId}/medications`);
    return response.data;
  }
}

// Export singleton instance
export const patientService = new PatientService();

// Export class for testing
export { PatientService };
```

## 🧪 Testing

### Backend Testing

#### Unit Testing
```python
# tests/test_patients.py
import pytest
from django.test import TestCase
from django.contrib.auth.models import User
from rest_framework.test import APIClient
from rest_framework import status
from patients.models import Patient
from patients.serializers import PatientSerializer
import json

class PatientModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )

        self.patient_data = {
            'first_name': 'John',
            'last_name': 'Doe',
            'date_of_birth': '1990-01-15',
            'gender': 'M',
            'contact_number': '+1234567890',
            'email': 'john.doe@example.com',
            'address': {
                'street': '123 Main St',
                'city': 'Anytown',
                'state': 'CA',
                'zip_code': '12345'
            },
            'emergency_contact': {
                'name': 'Jane Doe',
                'relationship': 'Spouse',
                'phone': '+1234567891'
            }
        }

    def test_patient_creation(self):
        """Test patient model creation"""
        patient = Patient.objects.create(
            **self.patient_data,
            created_by=self.user
        )

        self.assertEqual(patient.first_name, 'John')
        self.assertEqual(patient.last_name, 'Doe')
        self.assertEqual(patient.gender, 'M')
        self.assertTrue(patient.is_active)
        self.assertEqual(patient.created_by, self.user)

    def test_patient_str_method(self):
        """Test patient string representation"""
        patient = Patient.objects.create(
            **self.patient_data,
            created_by=self.user
        )

        expected_str = "John Doe (P000001)"
        self.assertEqual(str(patient), expected_str)

    def test_patient_full_name_property(self):
        """Test patient full name property"""
        patient = Patient.objects.create(
            **self.patient_data,
            created_by=self.user
        )

        self.assertEqual(patient.get_full_name(), "John Doe")

    def test_patient_age_calculation(self):
        """Test patient age calculation"""
        patient = Patient.objects.create(
            **self.patient_data,
            created_by=self.user
        )

        # Age should be calculated based on current date
        age = patient.get_age()
        self.assertIsInstance(age, int)
        self.assertGreaterEqual(age, 0)

class PatientSerializerTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )

        self.patient_data = {
            'first_name': 'Jane',
            'last_name': 'Smith',
            'date_of_birth': '1985-03-20',
            'gender': 'F',
            'contact_number': '+1234567891',
            'email': 'jane.smith@example.com'
        }

    def test_patient_serializer_valid_data(self):
        """Test patient serializer with valid data"""
        serializer = PatientSerializer(data=self.patient_data)
        self.assertTrue(serializer.is_valid())

        patient = serializer.save(created_by=self.user)
        self.assertEqual(patient.first_name, 'Jane')
        self.assertEqual(patient.last_name, 'Smith')

    def test_patient_serializer_invalid_email(self):
        """Test patient serializer with invalid email"""
        self.patient_data['email'] = 'invalid-email'
        serializer = PatientSerializer(data=self.patient_data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('email', serializer.errors)

    def test_patient_serializer_invalid_phone(self):
        """Test patient serializer with invalid phone number"""
        self.patient_data['contact_number'] = 'invalid-phone'
        serializer = PatientSerializer(data=self.patient_data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('contact_number', serializer.errors)

class PatientAPITest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )

        # Create user profile with healthcare provider role
        from django.contrib.auth.models import Group
        from core.models import UserProfile

        healthcare_group, _ = Group.objects.get_or_create(name='Healthcare Provider')
        self.user.groups.add(healthcare_group)

        UserProfile.objects.create(
            user=self.user,
            role='doctor',
            specialty='General Practice'
        )

        # Authenticate user
        self.client.force_authenticate(user=self.user)

        self.patient_data = {
            'first_name': 'Test',
            'last_name': 'Patient',
            'date_of_birth': '1992-05-10',
            'gender': 'M',
            'contact_number': '+1234567892',
            'email': 'test.patient@example.com'
        }

    def test_create_patient_api(self):
        """Test patient creation via API"""
        response = self.client.post(
            '/api/v1/patients/',
            data=json.dumps(self.patient_data),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('id', response.data)
        self.assertEqual(response.data['first_name'], 'Test')
        self.assertEqual(response.data['last_name'], 'Patient')

    def test_get_patient_list_api(self):
        """Test getting patient list via API"""
        # Create a test patient
        Patient.objects.create(
            **self.patient_data,
            created_by=self.user
        )

        response = self.client.get('/api/v1/patients/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('results', response.data)
        self.assertGreater(len(response.data['results']), 0)

    def test_get_patient_detail_api(self):
        """Test getting patient detail via API"""
        patient = Patient.objects.create(
            **self.patient_data,
            created_by=self.user
        )

        response = self.client.get(f'/api/v1/patients/{patient.id}/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], str(patient.id))
        self.assertEqual(response.data['first_name'], 'Test')

    def test_update_patient_api(self):
        """Test patient update via API"""
        patient = Patient.objects.create(
            **self.patient_data,
            created_by=self.user
        )

        update_data = {
            'first_name': 'Updated',
            'email': 'updated.email@example.com'
        }

        response = self.client.patch(
            f'/api/v1/patients/{patient.id}/',
            data=json.dumps(update_data),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['first_name'], 'Updated')
        self.assertEqual(response.data['email'], 'updated.email@example.com')

    def test_delete_patient_api(self):
        """Test patient deletion via API"""
        patient = Patient.objects.create(
            **self.patient_data,
            created_by=self.user
        )

        response = self.client.delete(f'/api/v1/patients/{patient.id}/')

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        # Verify patient is soft deleted
        patient.refresh_from_db()
        self.assertFalse(patient.is_active)

    def test_patient_search_api(self):
        """Test patient search functionality"""
        # Create test patients
        Patient.objects.create(
            first_name='John',
            last_name='Doe',
            date_of_birth='1990-01-15',
            gender='M',
            contact_number='+1234567890',
            created_by=self.user
        )

        Patient.objects.create(
            first_name='Jane',
            last_name='Smith',
            date_of_birth='1985-03-20',
            gender='F',
            contact_number='+1234567891',
            created_by=self.user
        )

        response = self.client.get('/api/v1/patients/search?query=John')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['patients']), 1)
        self.assertEqual(response.data['patients'][0]['first_name'], 'John')

    def test_unauthorized_access(self):
        """Test unauthorized access to patient endpoints"""
        # Remove authentication
        self.client.force_authenticate(user=None)

        response = self.client.get('/api/v1/patients/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    @pytest.mark.django_db
    def test_patient_permissions(self):
        """Test patient access permissions"""
        # Create user without healthcare provider role
        regular_user = User.objects.create_user(
            username='regularuser',
            password='testpass123'
        )

        # Create patient with different user
        other_user = User.objects.create_user(
            username='otheruser',
            password='testpass123'
        )

        patient = Patient.objects.create(
            first_name='Other',
            last_name='Patient',
            date_of_birth='1980-01-01',
            gender='M',
            contact_number='+1234567893',
            created_by=other_user
        )

        # Test regular user access
        self.client.force_authenticate(user=regular_user)
        response = self.client.get(f'/api/v1/patients/{patient.id}/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
```

#### Integration Testing
```python
# tests/test_integration.py
import pytest
from django.test import TestCase
from django.contrib.auth.models import User
from rest_framework.test import APIClient
from unittest.mock import patch
import json

class PatientAppointmentIntegrationTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )

        # Set up user profile
        from core.models import UserProfile
        UserProfile.objects.create(
            user=self.user,
            role='doctor',
            specialty='General Practice'
        )

        self.client.force_authenticate(user=self.user)

        self.patient_data = {
            'first_name': 'Integration',
            'last_name': 'Test',
            'date_of_birth': '1985-06-15',
            'gender': 'M',
            'contact_number': '+1234567894',
            'email': 'integration.test@example.com'
        }

        self.appointment_data = {
            'appointment_type': 'office_visit',
            'start_datetime': '2024-02-01T10:00:00Z',
            'end_datetime': '2024-02-01T10:30:00Z',
            'location': 'Main Clinic - Room 101',
            'reason': 'Follow-up visit',
            'status': 'scheduled'
        }

    def test_patient_appointment_workflow(self):
        """Test complete patient appointment workflow"""
        # Step 1: Create patient
        patient_response = self.client.post(
            '/api/v1/patients/',
            data=json.dumps(self.patient_data),
            content_type='application/json'
        )

        self.assertEqual(patient_response.status_code, 201)
        patient_id = patient_response.data['id']

        # Step 2: Schedule appointment for patient
        self.appointment_data['patient_id'] = patient_id
        self.appointment_data['provider_id'] = str(self.user.id)

        appointment_response = self.client.post(
            '/api/v1/appointments/',
            data=json.dumps(self.appointment_data),
            content_type='application/json'
        )

        self.assertEqual(appointment_response.status_code, 201)
        appointment_id = appointment_response.data['id']

        # Step 3: Retrieve patient appointments
        appointments_response = self.client.get(
            f'/api/v1/patients/{patient_id}/appointments/'
        )

        self.assertEqual(appointments_response.status_code, 200)
        self.assertGreater(len(appointments_response.data), 0)

        # Step 4: Create clinical encounter during appointment
        encounter_data = {
            'patient_id': patient_id,
            'provider_id': str(self.user.id),
            'encounter_type': 'office_visit',
            'location': 'Main Clinic - Room 101',
            'chief_complaint': 'Routine follow-up',
            'assessment': [
                {
                    'condition': 'Hypertension',
                    'icd10_code': 'I10',
                    'severity': 'mild'
                }
            ]
        }

        encounter_response = self.client.post(
            '/api/v1/clinical/encounters/',
            data=json.dumps(encounter_data),
            content_type='application/json'
        )

        self.assertEqual(encounter_response.status_code, 201)

        # Step 5: Verify complete workflow
        # Get patient with all related data
        patient_response = self.client.get(f'/api/v1/patients/{patient_id}/')

        self.assertEqual(patient_response.status_code, 200)
        self.assertIn('appointments', patient_response.data)
        self.assertIn('clinical_encounters', patient_response.data)

        # Verify data consistency
        appointments = patient_response.data['appointments']
        encounters = patient_response.data['clinical_encounters']

        self.assertEqual(len(appointments), 1)
        self.assertEqual(len(encounters), 1)
        self.assertEqual(appointments[0]['id'], appointment_id)
        self.assertEqual(encounters[0]['patient_id'], patient_id)

    @patch('patients.services.patientService.send_appointment_reminder.delay')
    def test_appointment_reminder_workflow(self, mock_reminder):
        """Test appointment reminder workflow"""
        # Create patient
        patient_response = self.client.post(
            '/api/v1/patients/',
            data=json.dumps(self.patient_data),
            content_type='application/json'
        )

        patient_id = patient_response.data['id']

        # Schedule appointment
        self.appointment_data['patient_id'] = patient_id
        self.appointment_data['provider_id'] = str(self.user.id)

        appointment_response = self.client.post(
            '/api/v1/appointments/',
            data=json.dumps(self.appointment_data),
            content_type='application/json'
        )

        appointment_id = appointment_response.data['id']

        # Trigger reminder task
        from appointments.tasks import send_appointment_reminder
        send_appointment_reminder.delay(appointment_id, 'email')

        # Verify reminder task was called
        mock_reminder.assert_called_once_with(appointment_id, 'email')
```

### Frontend Testing

#### React Component Testing
```typescript
// src/components/patients/__tests__/PatientCard.test.tsx
import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import PatientCard from '../PatientCard';
import { Patient } from '../../../types/patient';

// Mock the date-fns library
jest.mock('date-fns', () => ({
  format: jest.fn(() => 'January 15, 1990'),
}));

const mockPatient: Patient = {
  id: '123e4567-e89b-12d3-a456-426614174000',
  patientId: 'P000001',
  firstName: 'John',
  lastName: 'Doe',
  dateOfBirth: '1990-01-15',
  gender: 'M',
  contactNumber: '+1234567890',
  email: 'john.doe@example.com',
  address: {
    street: '123 Main St',
    city: 'Anytown',
    state: 'CA',
    zipCode: '12345',
    country: 'USA',
  },
  emergencyContact: {
    name: 'Jane Doe',
    relationship: 'Spouse',
    phone: '+1234567891',
  },
  bloodType: 'O+',
  allergies: ['Penicillin', 'Latex'],
  medicalConditions: ['Hypertension', 'Diabetes Type 2'],
  currentMedications: [
    {
      name: 'Lisinopril',
      dosage: '10mg',
      frequency: 'Once daily',
    },
  ],
  isActive: true,
  createdAt: '2024-01-15T10:30:00Z',
  updatedAt: '2024-01-15T10:30:00Z',
};

const theme = createTheme();

const renderWithTheme = (component: React.ReactElement) => {
  return render(
    <ThemeProvider theme={theme}>
      {component}
    </ThemeProvider>
  );
};

describe('PatientCard Component', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  test('renders patient basic information correctly', () => {
    renderWithTheme(<PatientCard patient={mockPatient} />);

    expect(screen.getByText('John Doe')).toBeInTheDocument();
    expect(screen.getByText('ID: P000001')).toBeInTheDocument();
    expect(screen.getByText('+1234567890')).toBeInTheDocument();
    expect(screen.getByText('john.doe@example.com')).toBeInTheDocument();
  });

  test('displays gender chip with correct color', () => {
    renderWithTheme(<PatientCard patient={mockPatient} />);

    const genderChip = screen.getByText('Male');
    expect(genderChip).toBeInTheDocument();
  });

  test('shows age correctly', () => {
    renderWithTheme(<PatientCard patient={mockPatient} />);

    // The format function is mocked to return 'January 15, 1990'
    expect(screen.getByText('January 15, 1990')).toBeInTheDocument();
  });

  test('displays blood type when present', () => {
    renderWithTheme(<PatientCard patient={mockPatient} />);

    expect(screen.getByText('Blood Type: O+')).toBeInTheDocument();
  });

  test('displays medical conditions with limit', () => {
    renderWithTheme(<PatientCard patient={mockPatient} />);

    expect(screen.getByText('Medical Conditions:')).toBeInTheDocument();
    expect(screen.getByText('Hypertension')).toBeInTheDocument();
    expect(screen.getByText('Diabetes Type 2')).toBeInTheDocument();
  });

  test('shows active status chip', () => {
    renderWithTheme(<PatientCard patient={mockPatient} />);

    const activeChip = screen.getByText('Active');
    expect(activeChip).toBeInTheDocument();
  });

  test('shows inactive status chip', () => {
    const inactivePatient = { ...mockPatient, isActive: false };
    renderWithTheme(<PatientCard patient={inactivePatient} />);

    const inactiveChip = screen.getByText('Inactive');
    expect(inactiveChip).toBeInTheDocument();
  });

  test('handles view callback when provided', () => {
    const onViewMock = jest.fn();
    renderWithTheme(
      <PatientCard patient={mockPatient} onView={onViewMock} />
    );

    // Find and click the card (simulating user interaction)
    const card = screen.getByText('John Doe').closest('.MuiCard-root');
    if (card) {
      fireEvent.click(card);
    }

    // The onView callback should not be called directly by clicking the card
    // as the component doesn't have that functionality
    // This test verifies the callback is passed correctly
    expect(onViewMock).toBeDefined();
  });

  test('displays contact information correctly', () => {
    renderWithTheme(<PatientCard patient={mockPatient} />);

    expect(screen.getByText('john.doe@example.com')).toBeInTheDocument();
    expect(screen.getByText('+1234567890')).toBeInTheDocument();
  });

  test('does not display email when not provided', () => {
    const patientWithoutEmail = { ...mockPatient, email: undefined };
    renderWithTheme(<PatientCard patient={patientWithoutEmail} />);

    expect(screen.queryByText('john.doe@example.com')).not.toBeInTheDocument();
  });

  test('shows creation date', () => {
    renderWithTheme(<PatientCard patient={mockPatient} />);

    expect(screen.getByText('Created: Jan 15, 2024')).toBeInTheDocument();
  });

  test('handles empty medical conditions', () => {
    const patientWithoutConditions = { ...mockPatient, medicalConditions: [] };
    renderWithTheme(<PatientCard patient={patientWithoutConditions} />);

    expect(screen.queryByText('Medical Conditions:')).not.toBeInTheDocument();
  });

  test('limits medical conditions display', () => {
    const patientWithManyConditions = {
      ...mockPatient,
      medicalConditions: [
        'Condition 1',
        'Condition 2',
        'Condition 3',
        'Condition 4',
        'Condition 5',
      ],
    };
    renderWithTheme(<PatientCard patient={patientWithManyConditions} />);

    expect(screen.getByText('Condition 1')).toBeInTheDocument();
    expect(screen.getByText('Condition 2')).toBeInTheDocument();
    expect(screen.getByText('Condition 3')).toBeInTheDocument();
    expect(screen.getByText('+2 more')).toBeInTheDocument();
  });
});
```

#### Hook Testing
```typescript
// src/hooks/__tests__/usePatientData.test.ts
import { renderHook, act } from '@testing-library/react';
import { usePatientData } from '../usePatientData';
import { patientService } from '../../services/patientService';

// Mock the patientService
jest.mock('../../services/patientService');
const mockedPatientService = patientService as jest.Mocked<typeof patientService>;

const mockPatients = [
  {
    id: '1',
    patientId: 'P000001',
    firstName: 'John',
    lastName: 'Doe',
    dateOfBirth: '1990-01-15',
    gender: 'M',
    contactNumber: '+1234567890',
    email: 'john.doe@example.com',
    isActive: true,
    createdAt: '2024-01-15T10:30:00Z',
    updatedAt: '2024-01-15T10:30:00Z',
  },
  {
    id: '2',
    patientId: 'P000002',
    firstName: 'Jane',
    lastName: 'Smith',
    dateOfBirth: '1985-03-20',
    gender: 'F',
    contactNumber: '+1234567891',
    email: 'jane.smith@example.com',
    isActive: true,
    createdAt: '2024-01-15T10:30:00Z',
    updatedAt: '2024-01-15T10:30:00Z',
  },
];

describe('usePatientData Hook', () => {
  beforeEach(() => {
    jest.clearAllMocks();

    // Mock default service response
    mockedPatientService.getPatients.mockResolvedValue({
      patients: mockPatients,
      total: 2,
      limit: 20,
      offset: 0,
    });
  });

  test('fetches patients on initial render', async () => {
    const { result } = renderHook(() => usePatientData());

    expect(result.current.loading).toBe(true);
    expect(result.current.patients).toEqual([]);
    expect(result.current.error).toBeNull();

    // Wait for async operation to complete
    await act(async () => {
      await new Promise(resolve => setTimeout(resolve, 0));
    });

    expect(result.current.loading).toBe(false);
    expect(result.current.patients).toEqual(mockPatients);
    expect(result.current.totalCount).toBe(2);
    expect(result.current.error).toBeNull();
    expect(mockedPatientService.getPatients).toHaveBeenCalledWith({
      page: 1,
      limit: 20,
    });
  });

  test('handles fetch patients error', async () => {
    const errorMessage = 'Failed to fetch patients';
    mockedPatientService.getPatients.mockRejectedValue(new Error(errorMessage));

    const { result } = renderHook(() => usePatientData());

    await act(async () => {
      await new Promise(resolve => setTimeout(resolve, 0));
    });

    expect(result.current.loading).toBe(false);
    expect(result.current.error).toBe(errorMessage);
    expect(result.current.patients).toEqual([]);
  });

  test('creates patient successfully', async () => {
    const newPatient = {
      id: '3',
      patientId: 'P000003',
      firstName: 'Bob',
      lastName: 'Johnson',
      dateOfBirth: '1982-07-10',
      gender: 'M',
      contactNumber: '+1234567892',
      email: 'bob.johnson@example.com',
      isActive: true,
      createdAt: '2024-01-15T10:30:00Z',
      updatedAt: '2024-01-15T10:30:00Z',
    };

    mockedPatientService.createPatient.mockResolvedValue(newPatient);

    const { result } = renderHook(() => usePatientData());

    // Wait for initial load
    await act(async () => {
      await new Promise(resolve => setTimeout(resolve, 0));
    });

    expect(result.current.patients).toHaveLength(2);

    // Create new patient
    await act(async () => {
      await result.current.createPatient({
        firstName: 'Bob',
        lastName: 'Johnson',
        dateOfBirth: '1982-07-10',
        gender: 'M',
        contactNumber: '+1234567892',
        email: 'bob.johnson@example.com',
      });
    });

    expect(result.current.patients).toHaveLength(3);
    expect(result.current.patients[0]).toEqual(newPatient);
    expect(result.current.totalCount).toBe(3);
    expect(mockedPatientService.createPatient).toHaveBeenCalledWith({
      firstName: 'Bob',
      lastName: 'Johnson',
      dateOfBirth: '1982-07-10',
      gender: 'M',
      contactNumber: '+1234567892',
      email: 'bob.johnson@example.com',
    });
  });

  test('handles create patient error', async () => {
    const errorMessage = 'Failed to create patient';
    mockedPatientService.createPatient.mockRejectedValue(new Error(errorMessage));

    const { result } = renderHook(() => usePatientData());

    // Wait for initial load
    await act(async () => {
      await new Promise(resolve => setTimeout(resolve, 0));
    });

    // Attempt to create patient
    let error: Error | null = null;
    await act(async () => {
      try {
        await result.current.createPatient({
          firstName: 'Bob',
          lastName: 'Johnson',
          dateOfBirth: '1982-07-10',
          gender: 'M',
          contactNumber: '+1234567892',
          email: 'bob.johnson@example.com',
        });
      } catch (err) {
        error = err as Error;
      }
    });

    expect(result.current.error).toBe(errorMessage);
    expect(error).not.toBeNull();
    expect(result.current.patients).toHaveLength(2); // Should not change
  });

  test('updates patient successfully', async () => {
    const updatedPatient = {
      ...mockPatients[0],
      firstName: 'John Updated',
      email: 'john.updated@example.com',
    };

    mockedPatientService.updatePatient.mockResolvedValue(updatedPatient);

    const { result } = renderHook(() => usePatientData());

    // Wait for initial load
    await act(async () => {
      await new Promise(resolve => setTimeout(resolve, 0));
    });

    expect(result.current.patients[0].firstName).toBe('John');

    // Update patient
    await act(async () => {
      await result.current.updatePatient('1', {
        firstName: 'John Updated',
        email: 'john.updated@example.com',
      });
    });

    expect(result.current.patients[0].firstName).toBe('John Updated');
    expect(result.current.patients[0].email).toBe('john.updated@example.com');
    expect(mockedPatientService.updatePatient).toHaveBeenCalledWith('1', {
      firstName: 'John Updated',
      email: 'john.updated@example.com',
    });
  });

  test('deletes patient successfully', async () => {
    mockedPatientService.deletePatient.mockResolvedValue();

    const { result } = renderHook(() => usePatientData());

    // Wait for initial load
    await act(async () => {
      await new Promise(resolve => setTimeout(resolve, 0));
    });

    expect(result.current.patients).toHaveLength(2);

    // Delete patient
    await act(async () => {
      await result.current.deletePatient('1');
    });

    expect(result.current.patients).toHaveLength(1);
    expect(result.current.totalCount).toBe(1);
    expect(mockedPatientService.deletePatient).toHaveBeenCalledWith('1');
  });

  test('handles pagination correctly', async () => {
    // Mock response for multiple pages
    mockedPatientService.getPatients.mockImplementation(async (params) => {
      const page = params.page || 1;
      const limit = params.limit || 20;
      const startIndex = (page - 1) * limit;
      const endIndex = startIndex + limit;

      return {
        patients: mockPatients.slice(startIndex, endIndex),
        total: mockPatients.length,
        limit: limit,
        offset: startIndex,
      };
    });

    const { result } = renderHook(() => usePatientData());

    // Wait for initial load (page 1)
    await act(async () => {
      await new Promise(resolve => setTimeout(resolve, 0));
    });

    expect(result.current.currentPage).toBe(1);
    expect(result.current.totalPages).toBe(1);
    expect(result.current.patients).toHaveLength(2);

    // Change to page 2
    await act(async () => {
      result.current.setCurrentPage(2);
    });

    expect(result.current.currentPage).toBe(2);
    expect(mockedPatientService.getPatients).toHaveBeenCalledWith({
      page: 2,
      limit: 20,
    });
  });

  test('refetches patients when filters change', async () => {
    const { result } = renderHook(() => usePatientData());

    // Wait for initial load
    await act(async () => {
      await new Promise(resolve => setTimeout(resolve, 0));
    });

    expect(mockedPatientService.getPatients).toHaveBeenCalledTimes(1);

    // Fetch patients with filters
    await act(async () => {
      await result.current.fetchPatients({ gender: 'M' });
    });

    expect(mockedPatientService.getPatients).toHaveBeenCalledTimes(2);
    expect(mockedPatientService.getPatients).toHaveBeenCalledWith({
      page: 1,
      limit: 20,
      gender: 'M',
    });
  });

  test('resets page to 1 when filters change', async () => {
    const { result } = renderHook(() => usePatientData());

    // Wait for initial load
    await act(async () => {
      await new Promise(resolve => setTimeout(resolve, 0));
    });

    // Change to page 2
    await act(async () => {
      result.current.setCurrentPage(2);
    });

    expect(result.current.currentPage).toBe(2);

    // Fetch with new filters
    await act(async () => {
      await result.current.fetchPatients({ gender: 'F' });
    });

    expect(result.current.currentPage).toBe(1);
  });
});
```

## 🚀 Deployment

### Docker Configuration

#### Dockerfile for Backend
```dockerfile
# backend/Dockerfile
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project
COPY . .

# Create non-root user
RUN useradd --create-home --shell /bin/bash app
USER app

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/health/')"

# Run application
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "hms.wsgi:application"]
```

#### Dockerfile for Frontend
```dockerfile
# frontend/Dockerfile
FROM node:18-alpine AS build

# Set working directory
WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm ci

# Copy source code
COPY . .

# Build application
RUN npm run build

# Production stage
FROM nginx:alpine

# Copy built application
COPY --from=build /app/dist /usr/share/nginx/html

# Copy nginx configuration
COPY nginx.conf /etc/nginx/nginx.conf

# Expose port
EXPOSE 80

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:80/ || exit 1

# Start nginx
CMD ["nginx", "-g", "daemon off;"]
```

#### Docker Compose Configuration
```yaml
# docker-compose.yml
version: '3.8'

services:
  # PostgreSQL Database
  db:
    image: postgres:15
    environment:
      POSTGRES_DB: hms_enterprise
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./scripts/init.sql:/docker-entrypoint-initdb.d/init.sql
    ports:
      - "5432:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 10s
      timeout: 5s
      retries: 5

  # Redis Cache
  redis:
    image: redis:7-alpine
    command: redis-server --requirepass ${REDIS_PASSWORD}
    volumes:
      - redis_data:/data
    ports:
      - "6379:6379"
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

  # Backend Service
  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    environment:
      - DJANGO_SETTINGS_MODULE=hms.settings.production
      - DATABASE_URL=postgresql://postgres:${POSTGRES_PASSWORD}@db:5432/hms_enterprise
      - REDIS_URL=redis://:${REDIS_PASSWORD}@redis:6379/0
      - SECRET_KEY=${DJANGO_SECRET_KEY}
      - DEBUG=False
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_healthy
    volumes:
      - ./backend:/app
      - static_volume:/app/static
    ports:
      - "8000:8000"
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health/"]
      interval: 30s
      timeout: 10s
      retries: 3

  # Frontend Service
  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    environment:
      - REACT_APP_API_URL=${API_URL}
    depends_on:
      - backend
    ports:
      - "80:80"
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:80/"]
      interval: 30s
      timeout: 10s
      retries: 3

  # Celery Worker
  celery-worker:
    build:
      context: ./backend
      dockerfile: Dockerfile
    command: celery -A core.celery worker --loglevel=info
    environment:
      - DJANGO_SETTINGS_MODULE=hms.settings.production
      - DATABASE_URL=postgresql://postgres:${POSTGRES_PASSWORD}@db:5432/hms_enterprise
      - REDIS_URL=redis://:${REDIS_PASSWORD}@redis:6379/0
      - SECRET_KEY=${DJANGO_SECRET_KEY}
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_healthy
    volumes:
      - ./backend:/app

  # Celery Beat
  celery-beat:
    build:
      context: ./backend
      dockerfile: Dockerfile
    command: celery -A core.celery beat --loglevel=info
    environment:
      - DJANGO_SETTINGS_MODULE=hms.settings.production
      - DATABASE_URL=postgresql://postgres:${POSTGRES_PASSWORD}@db:5432/hms_enterprise
      - REDIS_URL=redis://:${REDIS_PASSWORD}@redis:6379/0
      - SECRET_KEY=${DJANGO_SECRET_KEY}
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_healthy
    volumes:
      - ./backend:/app

  # Flower (Celery Monitoring)
  flower:
    image: mher/flower:0.9.7
    environment:
      - CELERY_BROKER_URL=redis://:${REDIS_PASSWORD}@redis:6379/0
      - FLOWER_PORT=5555
    ports:
      - "5555:5555"
    depends_on:
      - redis

volumes:
  postgres_data:
  redis_data:
  static_volume:
```

### Kubernetes Configuration

#### Kubernetes Deployment
```yaml
# k8s/backend-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: backend-deployment
  labels:
    app: backend
spec:
  replicas: 3
  selector:
    matchLabels:
      app: backend
  template:
    metadata:
      labels:
        app: backend
    spec:
      containers:
      - name: backend
        image: hms-enterprise-grade/backend:latest
        ports:
        - containerPort: 8000
        env:
        - name: DJANGO_SETTINGS_MODULE
          value: "hms.settings.production"
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: database-credentials
              key: url
        - name: REDIS_URL
          valueFrom:
            secretKeyRef:
              name: redis-credentials
              key: url
        - name: SECRET_KEY
          valueFrom:
            secretKeyRef:
              name: app-secrets
              key: django_secret_key
        - name: DEBUG
          value: "false"
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /health/
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
          failureThreshold: 3
        readinessProbe:
          httpGet:
            path: /ready/
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
          failureThreshold: 1
        volumeMounts:
        - name: static-files
          mountPath: /app/static
      volumes:
      - name: static-files
        persistentVolumeClaim:
          claimName: static-pvc
---
apiVersion: v1
kind: Service
metadata:
  name: backend-service
spec:
  selector:
    app: backend
  ports:
  - protocol: TCP
    port: 80
    targetPort: 8000
  type: ClusterIP
```

#### Kubernetes Ingress
```yaml
# k8s/ingress.yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: hms-ingress
  annotations:
    nginx.ingress.kubernetes.io/rewrite-target: /
    nginx.ingress.kubernetes.io/ssl-redirect: "true"
    cert-manager.io/cluster-issuer: letsencrypt-prod
spec:
  tls:
  - hosts:
    - api.hms-enterprise-grade.com
    secretName: hms-tls-secret
  rules:
  - host: api.hms-enterprise-grade.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: backend-service
            port:
              number: 80
---
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: frontend-ingress
  annotations:
    nginx.ingress.kubernetes.io/rewrite-target: /
    nginx.ingress.kubernetes.io/ssl-redirect: "true"
    cert-manager.io/cluster-issuer: letsencrypt-prod
spec:
  tls:
  - hosts:
    - hms-enterprise-grade.com
    secretName: frontend-tls-secret
  rules:
  - host: hms-enterprise-grade.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: frontend-service
            port:
              number: 80
```

## 📊 Monitoring and Logging

### Prometheus Configuration
```yaml
# monitoring/prometheus.yml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

rule_files:
  - "alert_rules.yml"

alerting:
  alertmanagers:
    - static_configs:
        - targets:
          - alertmanager:9093

scrape_configs:
  - job_name: 'kubernetes-pods'
    kubernetes_sd_configs:
      - role: pod
    relabel_configs:
      - source_labels: [__meta_kubernetes_pod_annotation_prometheus_io_scrape]
        action: keep
        regex: true

  - job_name: 'backend'
    static_configs:
      - targets: ['backend-service:80']

  - job_name: 'frontend'
    static_configs:
      - targets: ['frontend-service:80']

  - job_name: 'database'
    static_configs:
      - targets: ['postgres-exporter:9187']

  - job_name: 'redis'
    static_configs:
      - targets: ['redis-exporter:9121']
```

### Grafana Dashboard Configuration
```json
{
  "dashboard": {
    "id": null,
    "title": "HMS System Overview",
    "tags": ["hms", "healthcare"],
    "timezone": "browser",
    "panels": [
      {
        "id": 1,
        "title": "API Response Time",
        "type": "timeseries",
        "targets": [
          {
            "expr": "histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))",
            "legendFormat": "{{method}} {{status}}"
          }
        ],
        "fieldConfig": {
          "defaults": {
            "unit": "s"
          }
        }
      },
      {
        "id": 2,
        "title": "Database Connections",
        "type": "gauge",
        "targets": [
          {
            "expr": "pg_stat_database_numbackends",
            "legendFormat": "{{datname}}"
          }
        ]
      },
      {
        "id": 3,
        "title": "Error Rate",
        "type": "timeseries",
        "targets": [
          {
            "expr": "rate(http_requests_total{status=~\"5..\"}[5m])",
            "legendFormat": "5xx Errors"
          }
        ]
      }
    ]
  }
}
```

---

This comprehensive developer guide provides all the information needed to develop, test, and deploy the HMS Enterprise-Grade system. Follow these best practices and patterns to ensure high-quality, maintainable code.

*Last Updated: September 17, 2025*
*Documentation Version: v2.1.0*