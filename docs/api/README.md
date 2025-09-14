# API Documentation

The HMS uses REST APIs built with Django REST Framework and microservices with FastAPI. This document provides comprehensive API documentation for enterprise deployment.

## API Overview

### Backend API (Django REST Framework)
- **Base URL**: `http://backend:8000/api/`
- **Authentication**: JWT Bearer tokens
- **Format**: JSON
- **Schema**: OpenAPI 3.0 (Swagger)

### Microservices APIs (FastAPI)
- **Authentication**: JWT Bearer tokens
- **Format**: JSON
- **Schema**: OpenAPI 3.0

## Authentication

All APIs require authentication using JWT tokens obtained from the authentication service.

### Obtaining Access Token

```bash
POST /api/auth/token/
Content-Type: application/json

{
  "username": "your_username",
  "password": "your_password"
}
```

Response:
```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

### Using Access Token

Include the token in the Authorization header:
```
Authorization: Bearer <access_token>
```

## API Endpoints

### Core Endpoints

#### Health Check
- **GET** `/health/`
- **Description**: System health check
- **Response**: `{"status": "healthy"}`

#### API Schema
- **GET** `/api/schema/`
- **Description**: OpenAPI schema in JSON format

#### API Documentation
- **GET** `/api/docs/`
- **Description**: Interactive Swagger UI documentation

### Main API Categories

1. **Patients** (`/api/patients/`)
   - Patient management, demographics, medical history

2. **Appointments** (`/api/appointments/`)
   - Scheduling, resource management, waitlists

3. **EHR** (`/api/ehr/`)
   - Electronic Health Records, encounters, notes

4. **Billing** (`/api/billing/`)
   - Invoices, payments, service catalog

5. **Pharmacy** (`/api/pharmacy/`)
   - Medications, prescriptions, inventory

6. **Lab** (`/api/lab/`)
   - Lab tests, orders, results

7. **HR** (`/api/hr/`)
   - Staff management, shifts, leave requests

8. **Facilities** (`/api/facilities/`)
   - Wards, beds, resource allocation

9. **Accounting** (`/api/accounting/`)
   - Financial management, reports, compliance

10. **Analytics** (`/api/analytics/`)
    - Dashboard data, statistics, insights

## Microservices Endpoints

### Patients Service
- **Base URL**: `http://patients_service:8001`
- **Endpoints**: Patient CRUD operations

### Appointments Service
- **Base URL**: `http://appointments_service:8002`
- **Endpoints**: Appointment scheduling and management

### Billing Service
- **Base URL**: `http://billing_service:8003`
- **Endpoints**: Billing and payment processing

### Pharmacy Service
- **Base URL**: `http://pharmacy_service:8004`
- **Endpoints**: Medication management

### Lab Service
- **Base URL**: `http://lab_service:8005`
- **Endpoints**: Laboratory test management

### Analytics Service
- **Base URL**: `http://analytics_service:9010`
- **Endpoints**: Data analytics and reporting

### Notifications Service
- **Base URL**: `http://notifications_service:9011`
- **Endpoints**: Email, SMS, push notifications

### Audit Service
- **Base URL**: `http://audit_service:9015`
- **Endpoints**: Audit logging and compliance

## Error Handling

All APIs return standardized error responses:

```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable error message",
    "details": {}
  }
}
```

### Common HTTP Status Codes

- `200 OK`: Success
- `201 Created`: Resource created
- `400 Bad Request`: Invalid request data
- `401 Unauthorized`: Authentication required
- `403 Forbidden`: Insufficient permissions
- `404 Not Found`: Resource not found
- `422 Unprocessable Entity`: Validation errors
- `500 Internal Server Error`: Server error

## Rate Limiting

APIs implement rate limiting to prevent abuse:
- **Authenticated requests**: 1000/hour per user
- **Anonymous requests**: 100/hour per IP
- **Burst limit**: 50 requests/minute

## Pagination

List endpoints support pagination:

```json
{
  "count": 100,
  "next": "http://api.example.com/endpoint/?page=2",
  "previous": null,
  "results": [...]
}
```

Parameters:
- `page`: Page number (default: 1)
- `page_size`: Items per page (default: 25, max: 100)

## Filtering and Searching

Most list endpoints support filtering:

```bash
GET /api/patients/?search=john&age__gte=18&status=active
```

## Versioning

API versioning is handled through URL paths:
- Current version: v1 (implicit)
- Future versions: `/api/v2/endpoint/`

## Webhooks

The system supports webhooks for real-time notifications:

### Registering Webhooks

```bash
POST /api/webhooks/
Content-Type: application/json
Authorization: Bearer <token>

{
  "url": "https://your-app.com/webhook",
  "events": ["patient.created", "appointment.scheduled"],
  "secret": "your_webhook_secret"
}
```

### Supported Events

- `patient.created`
- `patient.updated`
- `appointment.scheduled`
- `appointment.cancelled`
- `billing.invoice.paid`
- `lab.result.ready`

## SDKs and Libraries

### Python Client

```python
from hms_client import HMSClient

client = HMSClient(
    base_url="http://backend:8000",
    token="your_jwt_token"
)

patients = client.patients.list(search="john")
```

### JavaScript Client

```javascript
import { HMSClient } from 'hms-client';

const client = new HMSClient({
  baseUrl: 'http://backend:8000',
  token: 'your_jwt_token'
});

const patients = await client.patients.list({ search: 'john' });
```

## Testing

Use the provided Postman collection or OpenAPI spec for testing:

```bash
# Generate OpenAPI spec
curl http://backend:8000/api/schema/ > openapi.json

# Use with testing tools
newman run hms-api-tests.postman_collection.json
```

## Monitoring

API performance is monitored through:

- **Prometheus metrics**: Response times, error rates
- **Grafana dashboards**: API usage visualization
- **Alerting**: Automatic alerts for API failures

## Security

- All communications use HTTPS in production
- API keys are encrypted and rotated regularly
- Input validation and sanitization
- SQL injection prevention
- XSS protection

## Support

For API support:
- Check the Swagger UI at `/api/docs/`
- Review error messages for detailed information
- Contact the development team for custom integrations
