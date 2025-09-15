# API Examples

This document provides detailed examples for common API operations in the HMS.

## Authentication

### Login

```bash
curl -X POST "http://backend:8000/api/auth/token/" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "doctor@example.com",
    "password": "securepassword123"
  }'
```

Response:
```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNjQ5NjY0NjAwLCJpYXQiOjE2NDk2NjQwMDAsImp0aSI6IjEyMzQ1Njc4OTAiLCJ1c2VyX2lkIjoxfQ.signature",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJ0b2tlbl90eXBlIjoicmVmcmVzaCIsImV4cCI6MTY1MjI1NjAwMCwiaWF0IjoxNjQ5NjY0MDAwLCJqdGkiOiIxMjM0NTY3ODkwIiwidXNlcl9pZCI6MX0.signature"
}
```

### Refresh Token

```bash
curl -X POST "http://backend:8000/api/auth/token/refresh/" \
  -H "Content-Type: application/json" \
  -d '{
    "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
  }'
```

## Patients

### Create Patient

```bash
curl -X POST "http://patients-service:8001/api/patients" \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "first_name": "John",
    "last_name": "Doe",
    "phone": "+1234567890",
    "email": "john.doe@example.com",
    "active": true
  }'
```

Response:
```json
{
  "id": 1,
  "first_name": "John",
  "last_name": "Doe",
  "phone": "+1234567890",
  "email": "john.doe@example.com",
  "active": true
}
```

### List Patients

```bash
curl -X GET "http://patients-service:8001/api/patients?page=1&page_size=10" \
  -H "Authorization: Bearer <access_token>"
```

Response:
```json
[
  {
    "id": 1,
    "first_name": "John",
    "last_name": "Doe",
    "phone": "+1234567890",
    "email": "john.doe@example.com",
    "active": true
  },
  {
    "id": 2,
    "first_name": "Jane",
    "last_name": "Smith",
    "phone": "+1987654321",
    "email": "jane.smith@example.com",
    "active": true
  }
]
```

## Appointments

### Schedule Appointment

```bash
curl -X POST "http://appointments-service:8002/api/appointments" \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "patient_id": 1,
    "doctor_id": 5,
    "appointment_date": "2024-01-15T10:00:00Z",
    "duration_minutes": 30,
    "appointment_type": "consultation",
    "notes": "Initial consultation for back pain"
  }'
```

Response:
```json
{
  "id": 123,
  "patient_id": 1,
  "doctor_id": 5,
  "appointment_date": "2024-01-15T10:00:00Z",
  "duration_minutes": 30,
  "status": "scheduled",
  "appointment_type": "consultation",
  "notes": "Initial consultation for back pain",
  "created_at": "2024-01-10T08:30:00Z"
}
```

### Get Appointments by Date

```bash
curl -X GET "http://appointments-service:8002/api/appointments?date=2024-01-15&doctor_id=5" \
  -H "Authorization: Bearer <access_token>"
```

## EHR (Electronic Health Records)

### Create Encounter

```bash
curl -X POST "http://backend:8000/api/ehr/encounters/" \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "patient": 1,
    "encounter_type": "office_visit",
    "encounter_date": "2024-01-15T10:00:00Z",
    "provider": 5,
    "chief_complaint": "Back pain for 2 weeks",
    "vital_signs": {
      "blood_pressure": "120/80",
      "heart_rate": 72,
      "temperature": 98.6,
      "weight": 180
    }
  }'
```

### Add Progress Note

```bash
curl -X POST "http://backend:8000/api/ehr/notes/" \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "encounter": 456,
    "note_type": "progress_note",
    "subjective": "Patient reports persistent lower back pain...",
    "objective": "Physical exam shows tenderness in lumbar region...",
    "assessment": "Acute lumbar strain",
    "plan": "Prescribe pain medication and physical therapy"
  }'
```

## Billing

### Create Invoice

```bash
curl -X POST "http://billing-service:8003/api/invoices" \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "patient_id": 1,
    "items": [
      {
        "description": "Office Visit - Level 3",
        "quantity": 1,
        "unit_price": 150.00,
        "service_code": "99213"
      },
      {
        "description": "X-Ray Lumbar Spine",
        "quantity": 1,
        "unit_price": 250.00,
        "service_code": "72100"
      }
    ],
    "due_date": "2024-02-15"
  }'
```

### Process Payment

```bash
curl -X PUT "http://billing-service:8003/api/invoices/789/pay" \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "payment_method": "credit_card",
    "amount": 400.00,
    "card_token": "tok_123456789"
  }'
```

## Pharmacy

### Create Prescription

```bash
curl -X POST "http://pharmacy-service:8004/api/prescriptions" \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "patient_id": 1,
    "provider_id": 5,
    "medication": "Ibuprofen 600mg",
    "dosage": "600mg every 8 hours",
    "quantity": 30,
    "refills": 2,
    "instructions": "Take with food. Do not exceed 2400mg per day."
  }'
```

### Dispense Medication

```bash
curl -X PUT "http://pharmacy-service:8004/api/prescriptions/101/dispense" \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "quantity_dispensed": 30,
    "days_supply": 10,
    "pharmacist_id": 12
  }'
```

## Lab

### Order Lab Test

```bash
curl -X POST "http://lab-service:8005/api/orders" \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "patient_id": 1,
    "provider_id": 5,
    "tests": [
      {
        "test_code": "CBC",
        "test_name": "Complete Blood Count",
        "priority": "routine"
      },
      {
        "test_code": "CMP",
        "test_name": "Comprehensive Metabolic Panel",
        "priority": "routine"
      }
    ],
    "collection_date": "2024-01-15T08:00:00Z",
    "specimen_type": "blood"
  }'
```

### Get Test Results

```bash
curl -X GET "http://lab-service:8005/api/results/202" \
  -H "Authorization: Bearer <access_token>"
```

Response:
```json
{
  "order_id": 202,
  "patient_id": 1,
  "results": [
    {
      "test_code": "CBC",
      "test_name": "Complete Blood Count",
      "status": "completed",
      "result_date": "2024-01-16T14:30:00Z",
      "values": [
        {
          "component": "WBC",
          "value": "7.2",
          "unit": "K/uL",
          "reference_range": "4.0-11.0",
          "flag": "normal"
        },
        {
          "component": "HGB",
          "value": "14.1",
          "unit": "g/dL",
          "reference_range": "12.0-16.0",
          "flag": "normal"
        }
      ]
    }
  ]
}
```

## Analytics

### Get Dashboard Data

```bash
curl -X GET "http://analytics-service:9010/api/dashboard?date_from=2024-01-01&date_to=2024-01-31" \
  -H "Authorization: Bearer <access_token>"
```

Response:
```json
{
  "total_patients": 1250,
  "new_patients_this_month": 45,
  "appointments_today": 28,
  "revenue_this_month": 125000.00,
  "average_wait_time": 15.5,
  "patient_satisfaction": 4.2,
  "department_utilization": {
    "emergency": 85,
    "cardiology": 92,
    "orthopedics": 78
  }
}
```

## Error Responses

### Authentication Error

```json
{
  "detail": "Authentication credentials were not provided."
}
```

Status: `401 Unauthorized`

### Permission Denied

```json
{
  "detail": "You do not have permission to perform this action."
}
```

Status: `403 Forbidden`

### Validation Error

```json
{
  "field_name": [
    "This field is required."
  ],
  "email": [
    "Enter a valid email address."
  ]
}
```

Status: `400 Bad Request`

### Not Found

```json
{
  "detail": "Not found."
}
```

Status: `404 Not Found`

### Rate Limit Exceeded

```json
{
  "detail": "Request was throttled. Expected available in 58 seconds."
}
```

Status: `429 Too Many Requests`

## Webhook Examples

### Register Webhook

```bash
curl -X POST "http://backend:8000/api/webhooks/" \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://your-app.com/webhook",
    "events": ["patient.created", "appointment.scheduled"],
    "secret": "your_webhook_secret"
  }'
```

### Webhook Payload

```json
{
  "event": "appointment.scheduled",
  "timestamp": "2024-01-15T10:00:00Z",
  "data": {
    "appointment_id": 123,
    "patient_id": 1,
    "doctor_id": 5,
    "appointment_date": "2024-01-15T10:30:00Z"
  },
  "signature": "sha256=abc123..."
}
```