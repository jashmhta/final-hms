# HMS Enterprise-Grade API Documentation

## 🌐 API Overview

The HMS Enterprise-Grade system provides comprehensive REST APIs for all healthcare operations. This document provides complete API reference documentation including endpoints, authentication, request/response formats, and examples.

### API Architecture

#### API Gateway
- **Base URL**: `https://api.hms-enterprise-grade.com/v1`
- **Protocol**: HTTPS only
- **Authentication**: JWT Bearer tokens
- **Rate Limiting**: 1000 requests per minute per user
- **Versioning**: Versioned endpoints (v1, v2, etc.)
- **Format**: JSON request/response format

#### API Standards
- **RESTful Design**: REST principles with proper HTTP methods
- **HATEOAS**: Hypermedia links for discoverability
- **JSON API**: JSON:API specification compliance
- **OpenAPI**: OpenAPI 3.0 specification
- **GraphQL**: GraphQL API for complex queries
- **WebSocket**: Real-time data streaming

### Authentication & Authorization

#### JWT Authentication
```http
POST /auth/token
Content-Type: application/json

{
  "username": "doctor_smith",
  "password": "secure_password",
  "mfa_code": "123456"
}
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "expires_in": 3600,
  "token_type": "Bearer",
  "scope": "read write"
}
```

#### Using API Tokens
```http
GET /api/v1/patients
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: application/json
```

### Rate Limiting
- **Default**: 1000 requests per minute
- **Burst**: 100 requests per second
- **Window**: 1 minute sliding window
- **Headers**: Rate limit information in response headers

```http
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 950
X-RateLimit-Reset: 1640995200
```

## 👥 Patient Management APIs

### Patient Endpoints

#### Create Patient
```http
POST /api/v1/patients
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "first_name": "John",
  "last_name": "Doe",
  "date_of_birth": "1990-01-15",
  "gender": "M",
  "contact_number": "+1234567890",
  "email": "john.doe@email.com",
  "address": {
    "street": "123 Main St",
    "city": "Anytown",
    "state": "CA",
    "zip_code": "12345",
    "country": "USA"
  },
  "emergency_contact": {
    "name": "Jane Doe",
    "relationship": "Spouse",
    "phone": "+1234567891"
  },
  "blood_type": "O+",
  "allergies": ["Penicillin", "Latex"],
  "medical_conditions": ["Hypertension", "Diabetes Type 2"],
  "current_medications": [
    {
      "name": "Lisinopril",
      "dosage": "10mg",
      "frequency": "Once daily"
    }
  ]
}
```

**Response:**
```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "patient_id": "P20240001",
  "first_name": "John",
  "last_name": "Doe",
  "date_of_birth": "1990-01-15",
  "gender": "M",
  "contact_number": "+1234567890",
  "email": "john.doe@email.com",
  "address": {
    "street": "123 Main St",
    "city": "Anytown",
    "state": "CA",
    "zip_code": "12345",
    "country": "USA"
  },
  "emergency_contact": {
    "name": "Jane Doe",
    "relationship": "Spouse",
    "phone": "+1234567891"
  },
  "blood_type": "O+",
  "allergies": ["Penicillin", "Latex"],
  "medical_conditions": ["Hypertension", "Diabetes Type 2"],
  "current_medications": [
    {
      "name": "Lisinopril",
      "dosage": "10mg",
      "frequency": "Once daily"
    }
  ],
  "is_active": true,
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T10:30:00Z",
  "_links": {
    "self": {
      "href": "https://api.hms-enterprise-grade.com/v1/patients/123e4567-e89b-12d3-a456-426614174000"
    },
    "clinical_encounters": {
      "href": "https://api.hms-enterprise-grade.com/v1/patients/123e4567-e89b-12d3-a456-426614174000/encounters"
    },
    "appointments": {
      "href": "https://api.hms-enterprise-grade.com/v1/patients/123e4567-e89b-12d3-a456-426614174000/appointments"
    }
  }
}
```

#### Get Patient
```http
GET /api/v1/patients/{patient_id}
Authorization: Bearer {access_token}
```

#### Update Patient
```http
PUT /api/v1/patients/{patient_id}
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "first_name": "John",
  "last_name": "Doe",
  "contact_number": "+1234567890",
  "email": "john.doe@email.com",
  "address": {
    "street": "456 Oak Ave",
    "city": "Anytown",
    "state": "CA",
    "zip_code": "12345",
    "country": "USA"
  }
}
```

#### Search Patients
```http
GET /api/v1/patients/search?query=John&limit=10&offset=0
Authorization: Bearer {access_token}
```

**Response:**
```json
{
  "patients": [
    {
      "id": "123e4567-e89b-12d3-a456-426614174000",
      "patient_id": "P20240001",
      "first_name": "John",
      "last_name": "Doe",
      "date_of_birth": "1990-01-15",
      "gender": "M",
      "contact_number": "+1234567890",
      "email": "john.doe@email.com"
    }
  ],
  "total": 1,
  "limit": 10,
  "offset": 0,
  "_links": {
    "self": {
      "href": "https://api.hms-enterprise-grade.com/v1/patients/search?query=John&limit=10&offset=0"
    },
    "next": null,
    "prev": null
  }
}
```

## 🏥 Clinical APIs

### Clinical Encounter Endpoints

#### Create Clinical Encounter
```http
POST /api/v1/clinical/encounters
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "patient_id": "123e4567-e89b-12d3-a456-426614174000",
  "encounter_type": "office_visit",
  "location": "Main Clinic - Room 101",
  "chief_complaint": "Patient presents with persistent headache for 3 days",
  "history_of_present_illness": "Patient reports gradual onset of headache over the past 3 days. Pain is localized to frontal region, described as throbbing, 6/10 intensity.",
  "review_of_systems": {
    "constitutional": "No fever, chills, or weight loss",
    "heent": "Headache as above, no visual changes, no hearing loss",
    "cardiovascular": "No chest pain, palpitations, or edema",
    "respiratory": "No shortness of breath or cough",
    "gastrointestinal": "No nausea, vomiting, or abdominal pain",
    "neurological": "Headache as above, no weakness or numbness"
  },
  "physical_examination": {
    "vital_signs": {
      "blood_pressure": "120/80",
      "heart_rate": 72,
      "respiratory_rate": 16,
      "temperature": 98.6,
      "oxygen_saturation": 98
    },
    "general": "Well-developed, well-nourished, no acute distress",
    "heent": "PERRLA, tympanic membranes normal, no sinus tenderness",
    "cardiovascular": "Regular rate and rhythm, no murmurs",
    "respiratory": "Clear to auscultation bilaterally",
    "neurological": "Alert and oriented x3, cranial nerves II-XII intact"
  },
  "assessment": [
    {
      "condition": "Tension Headache",
      "icd10_code": "G44.1",
      "severity": "mild",
      "onset": "acute",
      "notes": "Likely tension headache given history and normal examination"
    }
  ],
  "plan": [
    {
      "type": "medication",
      "description": "Acetaminophen 500mg every 6 hours as needed for headache",
      "reason": "Pain relief"
    },
    {
      "type": "education",
      "description": "Patient education on headache triggers and stress management",
      "reason": "Prevention"
    },
    {
      "type": "follow_up",
      "description": "Follow up in 2 weeks if symptoms persist",
      "reason": "Monitoring"
    }
  ],
  "diagnoses": [
    {
      "code": "G44.1",
      "description": "Tension headache",
      "type": "primary",
      "confirmed": true
    }
  ]
}
```

**Response:**
```json
{
  "id": "223e4567-e89b-12d3-a456-426614174001",
  "patient_id": "123e4567-e89b-12d3-a456-426614174000",
  "provider_id": "323e4567-e89b-12d3-a456-426614174001",
  "encounter_type": "office_visit",
  "location": "Main Clinic - Room 101",
  "chief_complaint": "Patient presents with persistent headache for 3 days",
  "history_of_present_illness": "Patient reports gradual onset of headache over the past 3 days. Pain is localized to frontal region, described as throbbing, 6/10 intensity.",
  "review_of_systems": {
    "constitutional": "No fever, chills, or weight loss",
    "heent": "Headache as above, no visual changes, no hearing loss",
    "cardiovascular": "No chest pain, palpitations, or edema",
    "respiratory": "No shortness of breath or cough",
    "gastrointestinal": "No nausea, vomiting, or abdominal pain",
    "neurological": "Headache as above, no weakness or numbness"
  },
  "physical_examination": {
    "vital_signs": {
      "blood_pressure": "120/80",
      "heart_rate": 72,
      "respiratory_rate": 16,
      "temperature": 98.6,
      "oxygen_saturation": 98
    },
    "general": "Well-developed, well-nourished, no acute distress",
    "heent": "PERRLA, tympanic membranes normal, no sinus tenderness",
    "cardiovascular": "Regular rate and rhythm, no murmurs",
    "respiratory": "Clear to auscultation bilaterally",
    "neurological": "Alert and oriented x3, cranial nerves II-XII intact"
  },
  "assessment": [
    {
      "condition": "Tension Headache",
      "icd10_code": "G44.1",
      "severity": "mild",
      "onset": "acute",
      "notes": "Likely tension headache given history and normal examination"
    }
  ],
  "plan": [
    {
      "type": "medication",
      "description": "Acetaminophen 500mg every 6 hours as needed for headache",
      "reason": "Pain relief"
    },
    {
      "type": "education",
      "description": "Patient education on headache triggers and stress management",
      "reason": "Prevention"
    },
    {
      "type": "follow_up",
      "description": "Follow up in 2 weeks if symptoms persist",
      "reason": "Monitoring"
    }
  ],
  "diagnoses": [
    {
      "code": "G44.1",
      "description": "Tension headache",
      "type": "primary",
      "confirmed": true
    }
  ],
  "status": "completed",
  "created_at": "2024-01-15T11:00:00Z",
  "updated_at": "2024-01-15T11:00:00Z",
  "_links": {
    "self": {
      "href": "https://api.hms-enterprise-grade.com/v1/clinical/encounters/223e4567-e89b-12d3-a456-426614174001"
    },
    "patient": {
      "href": "https://api.hms-enterprise-grade.com/v1/patients/123e4567-e89b-12d3-a456-426614174000"
    },
    "provider": {
      "href": "https://api.hms-enterprise-grade.com/v1/providers/323e4567-e89b-12d3-a456-426614174001"
    }
  }
}
```

#### Get Clinical Encounters
```http
GET /api/v1/clinical/encounters?patient_id={patient_id}&limit=10&offset=0
Authorization: Bearer {access_token}
```

#### Update Clinical Encounter
```http
PUT /api/v1/clinical/encounters/{encounter_id}
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "assessment": [
    {
      "condition": "Tension Headache",
      "icd10_code": "G44.1",
      "severity": "mild",
      "onset": "acute",
      "notes": "Follow-up confirms tension headache diagnosis"
    }
  ],
  "plan": [
    {
      "type": "medication",
      "description": "Continue Acetaminophen 500mg every 6 hours as needed for headache",
      "reason": "Pain relief"
    },
    {
      "type": "follow_up",
      "description": "Follow up in 1 month for routine checkup",
      "reason": "Routine care"
    }
  ]
}
```

## 💊 Pharmacy APIs

### Prescription Endpoints

#### Create Prescription
```http
POST /api/v1/pharmacy/prescriptions
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "patient_id": "123e4567-e89b-12d3-a456-426614174000",
  "provider_id": "323e4567-e89b-12d3-a456-426614174001",
  "medication": {
    "name": "Lisinopril",
    "strength": "10mg",
    "form": "tablet",
    "ndc": "12345-678-90"
  },
  "dosage": {
    "amount": 1,
    "unit": "tablet",
    "frequency": "once daily",
    "timing": "morning",
    "duration": 30,
    "duration_unit": "days",
    "instructions": "Take one tablet by mouth once daily in the morning",
    "indications": "Hypertension"
  },
  "substitutions": "allowed",
  "refills": {
    "authorized": 3,
    "remaining": 3
  },
  "pharmacy": {
    "name": "Main Street Pharmacy",
    "ncpdp": "1234567",
    "address": {
      "street": "123 Main St",
      "city": "Anytown",
      "state": "CA",
      "zip_code": "12345"
    },
    "phone": "+1234567890"
  },
  "diagnosis_codes": ["I10"],
  "notes": "Patient's blood pressure well controlled on current regimen",
  "controlled_substance": false,
  "dea_number": null
}
```

**Response:**
```json
{
  "id": "423e4567-e89b-12d3-a456-426614174002",
  "prescription_number": "RX20240001",
  "patient_id": "123e4567-e89b-12d3-a456-426614174000",
  "provider_id": "323e4567-e89b-12d3-a456-426614174001",
  "medication": {
    "name": "Lisinopril",
    "strength": "10mg",
    "form": "tablet",
    "ndc": "12345-678-90"
  },
  "dosage": {
    "amount": 1,
    "unit": "tablet",
    "frequency": "once daily",
    "timing": "morning",
    "duration": 30,
    "duration_unit": "days",
    "instructions": "Take one tablet by mouth once daily in the morning",
    "indications": "Hypertension"
  },
  "substitutions": "allowed",
  "refills": {
    "authorized": 3,
    "remaining": 3
  },
  "pharmacy": {
    "name": "Main Street Pharmacy",
    "ncpdp": "1234567",
    "address": {
      "street": "123 Main St",
      "city": "Anytown",
      "state": "CA",
      "zip_code": "12345"
    },
    "phone": "+1234567890"
  },
  "diagnosis_codes": ["I10"],
  "notes": "Patient's blood pressure well controlled on current regimen",
  "status": "active",
  "date_written": "2024-01-15T11:30:00Z",
  "expires_at": "2024-07-15T11:30:00Z",
  "controlled_substance": false,
  "dea_number": null,
  "created_at": "2024-01-15T11:30:00Z",
  "updated_at": "2024-01-15T11:30:00Z",
  "_links": {
    "self": {
      "href": "https://api.hms-enterprise-grade.com/v1/pharmacy/prescriptions/423e4567-e89b-12d3-a456-426614174002"
    },
    "patient": {
      "href": "https://api.hms-enterprise-grade.com/v1/patients/123e4567-e89b-12d3-a456-426614174000"
    },
    "provider": {
      "href": "https://api.hms-enterprise-grade.com/v1/providers/323e4567-e89b-12d3-a456-426614174001"
    }
  }
}
```

#### Drug Interaction Check
```http
POST /api/v1/pharmacy/drug-interactions
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "patient_id": "123e4567-e89b-12d3-a456-426614174000",
  "medications": [
    {
      "name": "Lisinopril",
      "ndc": "12345-678-90"
    },
    {
      "name": "Ibuprofen",
      "ndc": "09876-543-21"
    }
  ]
}
```

**Response:**
```json
{
  "interactions": [
    {
      "severity": "moderate",
      "interaction_type": "increased_risk",
      "description": "Lisinopril and Ibuprofen may increase the risk of kidney damage",
      "recommendation": "Monitor kidney function and blood pressure regularly",
      "references": [
        "DrugBank Interaction DB00072",
        "Lexicomp Interaction ID 12345"
      ]
    }
  ],
  "allergies": [
    {
      "medication": "Penicillin",
      "severity": "severe",
      "reaction": "Anaphylaxis"
    }
  ],
  "checked_at": "2024-01-15T11:35:00Z"
}
```

## 🧪 Laboratory APIs

### Laboratory Order Endpoints

#### Create Laboratory Order
```http
POST /api/v1/laboratory/orders
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "patient_id": "123e4567-e89b-12d3-a456-426614174000",
  "provider_id": "323e4567-e89b-12d3-a456-426614174001",
  "ordering_location": "Main Clinic",
  "priority": "routine",
  "clinical_information": "Annual physical examination",
  "tests": [
    {
      "test_code": "CMP",
      "test_name": "Comprehensive Metabolic Panel",
      "specimen_type": "serum",
      "collection_instructions": "Fasting for 12 hours"
    },
    {
      "test_code": "CBC",
      "test_name": "Complete Blood Count",
      "specimen_type": "whole_blood",
      "collection_instructions": "No special preparation required"
    },
    {
      "test_code": "LIP",
      "test_name": "Lipid Panel",
      "specimen_type": "serum",
      "collection_instructions": "Fasting for 12 hours"
    }
  ],
  "diagnoses": ["Z00.00"],
  "notes": "Routine annual physical",
  "collection_date": "2024-01-16T08:00:00Z"
}
```

**Response:**
```json
{
  "id": "523e4567-e89b-12d3-a456-426614174003",
  "order_number": "LAB20240001",
  "patient_id": "123e4567-e89b-12d3-a456-426614174000",
  "provider_id": "323e4567-e89b-12d3-a456-426614174001",
  "ordering_location": "Main Clinic",
  "priority": "routine",
  "clinical_information": "Annual physical examination",
  "tests": [
    {
      "test_code": "CMP",
      "test_name": "Comprehensive Metabolic Panel",
      "specimen_type": "serum",
      "collection_instructions": "Fasting for 12 hours",
      "status": "ordered"
    },
    {
      "test_code": "CBC",
      "test_name": "Complete Blood Count",
      "specimen_type": "whole_blood",
      "collection_instructions": "No special preparation required",
      "status": "ordered"
    },
    {
      "test_code": "LIP",
      "test_name": "Lipid Panel",
      "specimen_type": "serum",
      "collection_instructions": "Fasting for 12 hours",
      "status": "ordered"
    }
  ],
  "diagnoses": ["Z00.00"],
  "notes": "Routine annual physical",
  "status": "ordered",
  "ordered_at": "2024-01-15T12:00:00Z",
  "collection_date": "2024-01-16T08:00:00Z",
  "created_at": "2024-01-15T12:00:00Z",
  "updated_at": "2024-01-15T12:00:00Z",
  "_links": {
    "self": {
      "href": "https://api.hms-enterprise-grade.com/v1/laboratory/orders/523e4567-e89b-12d3-a456-426614174003"
    },
    "patient": {
      "href": "https://api.hms-enterprise-grade.com/v1/patients/123e4567-e89b-12d3-a456-426614174000"
    },
    "provider": {
      "href": "https://api.hms-enterprise-grade.com/v1/providers/323e4567-e89b-12d3-a456-426614174001"
    },
    "results": {
      "href": "https://api.hms-enterprise-grade.com/v1/laboratory/orders/523e4567-e89b-12d3-a456-426614174003/results"
    }
  }
}
```

#### Get Laboratory Results
```http
GET /api/v1/laboratory/orders/{order_id}/results
Authorization: Bearer {access_token}
```

**Response:**
```json
{
  "order_id": "523e4567-e89b-12d3-a456-426614174003",
  "patient_id": "123e4567-e89b-12d3-a456-426614174000",
  "results": [
    {
      "test_code": "CMP",
      "test_name": "Comprehensive Metabolic Panel",
      "components": [
        {
          "component": "Glucose",
          "result": "95",
          "unit": "mg/dL",
          "reference_range": "70-100",
          "flag": null,
          "status": "final"
        },
        {
          "component": "BUN",
          "result": "15",
          "unit": "mg/dL",
          "reference_range": "7-20",
          "flag": null,
          "status": "final"
        },
        {
          "component": "Creatinine",
          "result": "0.9",
          "unit": "mg/dL",
          "reference_range": "0.6-1.2",
          "flag": null,
          "status": "final"
        }
      ],
      "status": "completed",
      "resulted_at": "2024-01-16T10:30:00Z"
    },
    {
      "test_code": "CBC",
      "test_name": "Complete Blood Count",
      "components": [
        {
          "component": "WBC",
          "result": "7.5",
          "unit": "K/uL",
          "reference_range": "4.0-11.0",
          "flag": null,
          "status": "final"
        },
        {
          "component": "RBC",
          "result": "4.8",
          "unit": "M/uL",
          "reference_range": "4.2-5.4",
          "flag": null,
          "status": "final"
        },
        {
          "component": "Hemoglobin",
          "result": "14.5",
          "unit": "g/dL",
          "reference_range": "13.5-17.5",
          "flag": null,
          "status": "final"
        }
      ],
      "status": "completed",
      "resulted_at": "2024-01-16T10:30:00Z"
    }
  ],
  "status": "completed",
  "completed_at": "2024-01-16T10:30:00Z",
  "pathologist_id": "623e4567-e89b-12d3-a456-426614174004",
  "notes": "All results within normal limits",
  "created_at": "2024-01-16T10:30:00Z",
  "updated_at": "2024-01-16T10:30:00Z"
}
```

## 📅 Appointment APIs

### Appointment Endpoints

#### Create Appointment
```http
POST /api/v1/appointments
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "patient_id": "123e4567-e89b-12d3-a456-426614174000",
  "provider_id": "323e4567-e89b-12d3-a456-426614174001",
  "appointment_type": "office_visit",
  "start_datetime": "2024-01-20T14:00:00Z",
  "end_datetime": "2024-01-20T14:30:00Z",
  "location": "Main Clinic - Room 101",
  "reason": "Follow-up for hypertension",
  "status": "scheduled",
  "priority": "normal",
  "duration": 30,
  "notes": "Patient doing well on current medication regimen",
  "reminder_method": ["email", "sms"],
  "telehealth": false
}
```

**Response:**
```json
{
  "id": "623e4567-e89b-12d3-a456-426614174005",
  "appointment_number": "APT20240001",
  "patient_id": "123e4567-e89b-12d3-a456-426614174000",
  "provider_id": "323e4567-e89b-12d3-a456-426614174001",
  "appointment_type": "office_visit",
  "start_datetime": "2024-01-20T14:00:00Z",
  "end_datetime": "2024-01-20T14:30:00Z",
  "location": "Main Clinic - Room 101",
  "reason": "Follow-up for hypertension",
  "status": "scheduled",
  "priority": "normal",
  "duration": 30,
  "notes": "Patient doing well on current medication regimen",
  "reminder_method": ["email", "sms"],
  "telehealth": false,
  "created_at": "2024-01-15T13:00:00Z",
  "updated_at": "2024-01-15T13:00:00Z",
  "_links": {
    "self": {
      "href": "https://api.hms-enterprise-grade.com/v1/appointments/623e4567-e89b-12d3-a456-426614174005"
    },
    "patient": {
      "href": "https://api.hms-enterprise-grade.com/v1/patients/123e4567-e89b-12d3-a456-426614174000"
    },
    "provider": {
      "href": "https://api.hms-enterprise-grade.com/v1/providers/323e4567-e89b-12d3-a456-426614174001"
    }
  }
}
```

#### Get Provider Schedule
```http
GET /api/v1/appointments/schedule?provider_id={provider_id}&start_date=2024-01-20&end_date=2024-01-20
Authorization: Bearer {access_token}
```

**Response:**
```json
{
  "provider_id": "323e4567-e89b-12d3-a456-426614174001",
  "start_date": "2024-01-20",
  "end_date": "2024-01-20",
  "schedule": [
    {
      "id": "623e4567-e89b-12d3-a456-426614174005",
      "appointment_number": "APT20240001",
      "start_datetime": "2024-01-20T14:00:00Z",
      "end_datetime": "2024-01-20T14:30:00Z",
      "patient_id": "123e4567-e89b-12d3-a456-426614174000",
      "patient_name": "John Doe",
      "appointment_type": "office_visit",
      "location": "Main Clinic - Room 101",
      "status": "scheduled",
      "duration": 30
    }
  ],
  "available_slots": [
    {
      "start_time": "2024-01-20T08:00:00Z",
      "end_time": "2024-01-20T08:30:00Z",
      "duration": 30
    },
    {
      "start_time": "2024-01-20T08:30:00Z",
      "end_time": "2024-01-20T09:00:00Z",
      "duration": 30
    }
  ]
}
```

## 💰 Billing APIs

### Billing Charge Endpoints

#### Create Billing Charge
```http
POST /api/v1/billing/charges
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "patient_id": "123e4567-e89b-12d3-a456-426614174000",
  "encounter_id": "223e4567-e89b-12d3-a456-426614174001",
  "charge_date": "2024-01-15T11:00:00Z",
  "charge_code": "99213",
  "description": "Office visit, established patient",
  "quantity": 1,
  "unit_price": 100.00,
  "total_amount": 100.00,
  "insurance_amount": 80.00,
  "patient_amount": 20.00,
  "billing_provider_id": "323e4567-e89b-12d3-a456-426614174001",
  "diagnosis_codes": ["G44.1"],
  "modifiers": [],
  "notes": "Routine office visit for headache"
}
```

**Response:**
```json
{
  "id": "723e4567-e89b-12d3-a456-426614174006",
  "charge_number": "CHG20240001",
  "patient_id": "123e4567-e89b-12d3-a456-426614174000",
  "encounter_id": "223e4567-e89b-12d3-a456-426614174001",
  "charge_date": "2024-01-15T11:00:00Z",
  "charge_code": "99213",
  "description": "Office visit, established patient",
  "quantity": 1,
  "unit_price": 100.00,
  "total_amount": 100.00,
  "insurance_amount": 80.00,
  "patient_amount": 20.00,
  "status": "pending",
  "billing_provider_id": "323e4567-e89b-12d3-a456-426614174001",
  "diagnosis_codes": ["G44.1"],
  "modifiers": [],
  "notes": "Routine office visit for headache",
  "created_at": "2024-01-15T13:30:00Z",
  "updated_at": "2024-01-15T13:30:00Z",
  "_links": {
    "self": {
      "href": "https://api.hms-enterprise-grade.com/v1/billing/charges/723e4567-e89b-12d3-a456-426614174006"
    },
    "patient": {
      "href": "https://api.hms-enterprise-grade.com/v1/patients/123e4567-e89b-12d3-a456-426614174000"
    },
    "encounter": {
      "href": "https://api.hms-enterprise-grade.com/v1/clinical/encounters/223e4567-e89b-12d3-a456-426614174001"
    }
  }
}
```

#### Submit Insurance Claim
```http
POST /api/v1/billing/claims
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "patient_id": "123e4567-e89b-12d3-a456-426614174000",
  "insurance_provider": "Blue Cross Blue Shield",
  "policy_number": "BCBS123456789",
  "group_number": "GRP987654",
  "charges": [
    "723e4567-e89b-12d3-a456-426614174006"
  ],
  "total_amount": 100.00,
  "patient_responsibility": 20.00,
  "submission_method": "electronic",
  "diagnoses": ["G44.1"]
}
```

## 📊 Analytics APIs

### Analytics Endpoints

#### Get Patient Analytics
```http
GET /api/v1/analytics/patients?start_date=2024-01-01&end_date=2024-01-31&metrics=registrations,visits,revenue
Authorization: Bearer {access_token}
```

**Response:**
```json
{
  "start_date": "2024-01-01",
  "end_date": "2024-01-31",
  "metrics": {
    "registrations": {
      "total": 45,
      "new": 45,
      "growth_rate": 12.5
    },
    "visits": {
      "total": 234,
      "unique_patients": 189,
      "average_duration": 25.5
    },
    "revenue": {
      "total": 45678.90,
      "insurance": 36543.12,
      "patient": 9135.78,
      "growth_rate": 8.3
    }
  },
  "demographics": {
    "age_groups": {
      "0-18": 12,
      "19-35": 18,
      "36-50": 25,
      "51-65": 30,
      "65+": 15
    },
    "gender": {
      "male": 48,
      "female": 52,
      "other": 0
    },
    "insurance_types": {
      "private": 65,
      "medicare": 20,
      "medicaid": 10,
      "self_pay": 5
    }
  }
}
```

#### Get Clinical Quality Metrics
```http
GET /api/v1/analytics/clinical-quality?start_date=2024-01-01&end_date=2024-01-31
Authorization: Bearer {access_token}
```

**Response:**
```json
{
  "start_date": "2024-01-01",
  "end_date": "2024-01-31",
  "metrics": {
    "blood_pressure_control": {
      "eligible": 156,
      "controlled": 142,
      "rate": 91.0,
      "target": 90.0,
      "status": "met"
    },
    "diabetes_hba1c_control": {
      "eligible": 89,
      "controlled": 76,
      "rate": 85.4,
      "target": 85.0,
      "status": "met"
    },
    "cancer_screening": {
      "eligible": 234,
      "screened": 198,
      "rate": 84.6,
      "target": 80.0,
      "status": "met"
    },
    "medication_reconciliation": {
      "eligible": 456,
      "reconciled": 445,
      "rate": 97.6,
      "target": 95.0,
      "status": "met"
    }
  }
}
```

## 🔄 WebSocket APIs

### Real-time Events

#### Connect to WebSocket
```javascript
// WebSocket connection
const ws = new WebSocket('wss://api.hms-enterprise-grade.com/v1/ws');

// Authentication
ws.send(JSON.stringify({
  type: 'auth',
  token: 'your_jwt_token'
}));

// Subscribe to events
ws.send(JSON.stringify({
  type: 'subscribe',
  channels: ['patient_updates', 'appointment_changes', 'lab_results']
}));

// Handle messages
ws.onmessage = function(event) {
  const data = JSON.parse(event.data);

  switch(data.type) {
    case 'patient_updated':
      console.log('Patient updated:', data.patient);
      break;
    case 'appointment_scheduled':
      console.log('New appointment:', data.appointment);
      break;
    case 'lab_result_available':
      console.log('Lab result available:', data.result);
      break;
  }
};
```

## 🛠️ GraphQL API

### GraphQL Queries

#### Patient Query
```graphql
query GetPatient($id: ID!) {
  patient(id: $id) {
    id
    patientId
    firstName
    lastName
    dateOfBirth
    gender
    contactNumber
    email
    address {
      street
      city
      state
      zipCode
      country
    }
    clinicalEncounters {
      id
      encounterType
      encounterDate
      location
      chiefComplaint
      diagnoses {
        code
        description
      }
      provider {
        id
        firstName
        lastName
        specialty
      }
    }
    appointments {
      id
      startDateTime
      endDateTime
      appointmentType
      location
      status
      provider {
        id
        firstName
        lastName
      }
    }
    prescriptions {
      id
      medication {
        name
        strength
        form
      }
      dosage {
        amount
        unit
        frequency
        instructions
      }
      status
      dateWritten
    }
  }
}
```

#### Clinical Encounter Mutation
```graphql
mutation CreateClinicalEncounter($input: CreateClinicalEncounterInput!) {
  createClinicalEncounter(input: $input) {
    id
    patientId
    encounterType
    encounterDate
    chiefComplaint
    assessment {
      condition
      icd10Code
      severity
    }
    plan {
      type
      description
      reason
    }
    status
    createdAt
  }
}
```

## 🔒 Error Handling

### Error Response Format
```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid request data",
    "details": {
      "field": "email",
      "error": "Invalid email format"
    },
    "timestamp": "2024-01-15T14:30:00Z",
    "request_id": "req_123456789"
  }
}
```

### Common Error Codes
- `400` - Bad Request
- `401` - Unauthorized
- `403` - Forbidden
- `404` - Not Found
- `409` - Conflict
- `422` - Validation Error
- `429` - Too Many Requests
- `500` - Internal Server Error
- `503` - Service Unavailable

## 📝 API Usage Examples

### Python Example
```python
import requests
import json

class HMSAPIClient:
    def __init__(self, base_url, api_key):
        self.base_url = base_url
        self.api_key = api_key
        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        })

    def create_patient(self, patient_data):
        """Create a new patient"""
        response = self.session.post(
            f'{self.base_url}/api/v1/patients',
            json=patient_data
        )
        response.raise_for_status()
        return response.json()

    def get_patient(self, patient_id):
        """Get patient by ID"""
        response = self.session.get(
            f'{self.base_url}/api/v1/patients/{patient_id}'
        )
        response.raise_for_status()
        return response.json()

    def create_appointment(self, appointment_data):
        """Create new appointment"""
        response = self.session.post(
            f'{self.base_url}/api/v1/appointments',
            json=appointment_data
        )
        response.raise_for_status()
        return response.json()

# Usage example
client = HMSAPIClient('https://api.hms-enterprise-grade.com', 'your_api_key')

# Create patient
patient_data = {
    'first_name': 'John',
    'last_name': 'Doe',
    'date_of_birth': '1990-01-15',
    'gender': 'M',
    'contact_number': '+1234567890',
    'email': 'john.doe@email.com'
}

patient = client.create_patient(patient_data)
print(f"Created patient: {patient['patient_id']}")

# Create appointment
appointment_data = {
    'patient_id': patient['id'],
    'provider_id': '323e4567-e89b-12d3-a456-426614174001',
    'appointment_type': 'office_visit',
    'start_datetime': '2024-01-20T14:00:00Z',
    'end_datetime': '2024-01-20T14:30:00Z',
    'location': 'Main Clinic - Room 101',
    'reason': 'Follow-up visit'
}

appointment = client.create_appointment(appointment_data)
print(f"Created appointment: {appointment['appointment_number']}")
```

### JavaScript Example
```javascript
class HMSAPI {
    constructor(baseURL, apiKey) {
        this.baseURL = baseURL;
        this.apiKey = apiKey;
        this.headers = {
            'Authorization': `Bearer ${this.apiKey}`,
            'Content-Type': 'application/json'
        };
    }

    async request(endpoint, options = {}) {
        const url = `${this.baseURL}${endpoint}`;
        const config = {
            headers: this.headers,
            ...options
        };

        try {
            const response = await fetch(url, config);

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.error.message);
            }

            return await response.json();
        } catch (error) {
            console.error('API Error:', error);
            throw error;
        }
    }

    async createPatient(patientData) {
        return await this.request('/api/v1/patients', {
            method: 'POST',
            body: JSON.stringify(patientData)
        });
    }

    async getPatient(patientId) {
        return await this.request(`/api/v1/patients/${patientId}`);
    }

    async getAppointments(filters = {}) {
        const params = new URLSearchParams(filters);
        return await this.request(`/api/v1/appointments?${params}`);
    }
}

// Usage example
const api = new HMSAPI('https://api.hms-enterprise-grade.com', 'your_api_key');

// Create patient
const patientData = {
    firstName: 'Jane',
    lastName: 'Smith',
    dateOfBirth: '1985-03-20',
    gender: 'F',
    contactNumber: '+1234567891',
    email: 'jane.smith@email.com'
};

api.createPatient(patientData)
    .then(patient => {
        console.log('Created patient:', patient.patientId);
        return api.getAppointments({ patientId: patient.id });
    })
    .then(appointments => {
        console.log('Patient appointments:', appointments);
    })
    .catch(error => {
        console.error('Error:', error.message);
    });
```

---

This comprehensive API documentation provides complete reference information for all HMS Enterprise-Grade system APIs. All endpoints are secured with JWT authentication and include comprehensive error handling, rate limiting, and monitoring.

*Last Updated: September 17, 2025*
*API Version: v1.0.0*