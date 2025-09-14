# Insurance TPA Integration Module

Enterprise-grade Django REST Framework implementation for healthcare insurance TPA (Third Party Administrator) management.

## Features

- **Secure API Endpoints**: Token authentication, rate limiting, XSS protection
- **Pydantic Validation**: Strict input validation with business rule enforcement
- **Field Encryption**: Fernet-based encryption for sensitive patient data
- **Async Processing**: Celery integration for TPA request submission
- **Redis Caching**: High-performance status polling and data caching
- **Mock TPA Service**: Realistic Flask-based mock service for development/testing
- **API Versioning**: URL-based versioning for future compatibility
- **Comprehensive Logging**: Structured logging with file and console output

## API Endpoints

### Pre-Authorization
- `POST /api/v1/insurance/pre-auth/create/` - Create pre-auth request
- `GET /api/v1/insurance/pre-auth/` - List pre-auth requests
- `GET/PUT/DELETE /api/v1/insurance/pre-auth/<id>/` - Retrieve/update/delete

### Claims
- `POST /api/v1/insurance/claims/create/` - Create claim
- `GET /api/v1/insurance/claims/` - List claims
- `GET /api/v1/insurance/claims/<id>/` - Retrieve claim
- `GET /api/v1/insurance/claims/<id>/status/` - Get claim status (cached)

### Reimbursements
- `POST /api/v1/insurance/reimbursement/create/` - Create reimbursement
- `GET /api/v1/insurance/reimbursement/` - List reimbursements

### Mock TPA Service (Development)
- `POST http://localhost:5000/api/tpa/pre-auth/` - Mock pre-auth processing
- `POST http://localhost:5000/api/tpa/claim/` - Mock claim processing
- `GET http://localhost:5000/api/tpa/status/<id>/` - Get transaction status
- `GET http://localhost:5000/api/tpa/transactions` - List recent transactions

## Setup Instructions

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure Environment Variables
```bash
# Generate encryption key
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"

export DJANGO_ENCRYPTION_KEY='your_generated_key_here'
export MOCK_TPA_ENCRYPTION_KEY='your_generated_key_here'

# Database (PostgreSQL recommended)
export DB_NAME=hms_db
export DB_USER=hms_user
export DB_PASSWORD=hms_password
export DB_HOST=localhost
export DB_PORT=5432
```

### 3. Django Configuration

Add to `settings.py`:
```python
# Include the settings_integration.py content

# Add to INSTALLED_APPS
INSTALLED_APPS = [
    # ... other apps
    'rest_framework',
    'rest_framework.authtoken',
    'django_ratelimit',
    'app',  # Your TPA app
]

# URL Configuration in main urls.py
urlpatterns = [
    # ... other patterns
    path('api/', include('app.urls')),
]
```

### 4. Database Setup
```bash
python manage.py makemigrations app
python manage.py migrate
python manage.py createsuperuser
```

### 5. Start Services

**Django Development Server:**
```bash
python manage.py runserver 0.0.0.0:8000
```

**Redis (if not running):**
```bash
redis-server
```

**Celery Worker:**
```bash
celery -A your_project worker -l info
```

**Mock TPA Service:**
```bash
cd /root/hms-enterprise-grade/services/insurance_tpa_integration/api/
python mock_tpa.py
```

## Security Features

- **Authentication**: Token-based authentication required for all endpoints
- **Rate Limiting**:
  - Pre-auth: 5 requests/minute per user
  - Claims: 3 requests/minute per user
  - Reimbursements: 2 requests/minute per user
- **Input Validation**: Pydantic models with comprehensive validation
- **Data Encryption**: Fernet encryption for sensitive patient data
- **SQL Injection Protection**: Django ORM usage
- **XSS Prevention**: Django security middleware
- **CSRF Protection**: Django CSRF middleware

## Testing

### API Testing
```bash
# Test pre-auth creation
curl -X POST http://localhost:8000/api/v1/insurance/pre-auth/create/   -H "Authorization: Token your_token_here"   -H "Content-Type: application/json"   -d '{"patient_id":"PAT001","policy_number":"POL12345","procedure_code":"PROC001","estimated_amount":2500.00,"diagnosis_code":"DX001"}'

# Test claim status (cached)
curl -X GET "http://localhost:8000/api/v1/insurance/claims/1/status/"   -H "Authorization: Token your_token_here"
```

### Mock TPA Testing
```bash
# Test mock pre-auth
curl -X POST http://localhost:5000/api/tpa/pre-auth/   -H "Content-Type: application/json"   -d '{"patient_id":"PAT001","policy_number":"POL12345","procedure_code":"PROC001","estimated_amount":2500.00}'

# Test mock claim processing
curl -X POST http://localhost:5000/api/tpa/claim/   -H "Content-Type: application/json"   -d '{"patient_id":"PAT001","policy_number":"POL12345","claim_amount":4500.00,"procedure_codes":["PROC001","PROC002"]}'
```

## Production Deployment

### Docker Configuration

**Dockerfile for Django App:**
```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

EXPOSE 8000
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
```

**Docker Compose for Full Stack:**
```yaml
version: '3.8'
services:
  redis:
    image: redis:alpine
    ports:
      - "6379:6379"

  postgres:
    image: postgres:15
    environment:
      POSTGRES_DB: hms_db
      POSTGRES_USER: hms_user
      POSTGRES_PASSWORD: hms_password
    ports:
      - "5432:5432"

  django:
    build: .
    ports:
      - "8000:8000"
    depends_on:
      - redis
      - postgres
    environment:
      - DJANGO_ENCRYPTION_KEY=${DJANGO_ENCRYPTION_KEY}
      - DATABASE_URL=postgresql://hms_user:hms_password@postgres:5432/hms_db

  celery:
    build: .
    command: celery -A your_project worker -l info
    depends_on:
      - redis
      - django
    environment:
      - DJANGO_ENCRYPTION_KEY=${DJANGO_ENCRYPTION_KEY}

  mock-tpa:
    build: ./api
    ports:
      - "5000:5000"
    environment:
      - MOCK_TPA_ENCRYPTION_KEY=${MOCK_TPA_ENCRYPTION_KEY}
```

### Monitoring and Logging

- **Health Checks**: `/health` endpoint on Mock TPA service
- **Structured Logging**: JSON format for log aggregation
- **Metrics**: Redis cache hit/miss rates, API response times
- **Alerting**: Rate limit breaches, encryption failures

## Business Logic

### Pre-Authorization Flow
1. **Submission**: Patient data encrypted, request queued via Celery
2. **Validation**: Pydantic schema validation + business rules
3. **TPA Processing**: Mock service simulates 2-5 second approval/rejection
4. **Response**: Status cached in Redis, webhook notifications

### Claim Processing Flow
1. **Submission**: Multi-procedure claim with amount validation
2. **Async Processing**: Celery task handles TPA integration
3. **Reimbursement Calculation**: 90% max reimbursement rate
4. **Status Tracking**: Real-time status via Redis cache polling

### Security Model
- **Data at Rest**: Fernet encryption for PII fields
- **Data in Transit**: HTTPS/TLS encryption
- **Access Control**: Token auth + user-specific data filtering
- **Rate Limiting**: Per-endpoint throttling to prevent abuse

## Troubleshooting

### Common Issues

1. **Encryption Key Errors**
```bash
# Generate new key
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

2. **Redis Connection Issues**
```bash
# Test Redis connection
redis-cli ping
```

3. **Celery Worker Not Starting**
```bash
# Check broker connection
celery -A your_project inspect active
```

4. **Rate Limiting Not Working**
```bash
# Verify django-ratelimit configuration in settings
python manage.py shell
>>> from django_ratelimit.decorators import ratelimit
```

## Next Steps

1. **Integration Testing**: Test full workflow from pre-auth to reimbursement
2. **Performance Testing**: Load test with 1000+ concurrent requests
3. **Security Audit**: External penetration testing for production
4. **Monitoring Setup**: Integrate with Prometheus/Grafana for metrics
5. **CI/CD Pipeline**: Automate deployment with GitHub Actions

---

*Enterprise-grade implementation for secure healthcare financial APIs*
