# Insurance TPA Management Module

[![Build Status](https://img.shields.io/badge/build-passing-brightgreen.svg)](https://github.com/example/hms-enterprise)
[![Coverage](https://img.shields.io/badge/coverage-90%2B-brightgreen.svg)](https://github.com/example/hms-enterprise)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

Enterprise-grade Django REST Framework module for secure healthcare insurance Third Party Administrator (TPA) integration. Features field-level financial encryption, audit logging, Celery task processing, Redis caching, and comprehensive API documentation.

## 🚀 Features

- **🔒 Security**: Fernet encryption for all financial data, audit logging, rate limiting, token authentication
- **⚡ Performance**: Redis caching (1hr TTL), Celery async processing, database indexing
- **📊 Compliance**: HIPAA/GDPR ready, 365-day retention policy, immutable audit trail
- **🔄 Integration**: Mock TPA service, realistic approval rates (70% pre-auth, 90% claims)
- **🧪 Testing**: >90% coverage with pytest, factory-boy fixtures, integration tests
- **📖 Documentation**: OpenAPI schema, ADR documentation, comprehensive API examples

## 🛠️ Prerequisites

- Python 3.12+
- PostgreSQL 13+
- Redis 7+
- Docker & Docker Compose (recommended for development)

## 📦 Installation

### 1. Clone Repository
```bash
cd /root
mkdir -p hms-enterprise-grade/services
git clone https://github.com/example/hms-enterprise-grade.git
cd hms-enterprise-grade/services/insurance_tpa_integration
```

### 2. Virtual Environment Setup
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate  # Windows
pip install --upgrade pip
pip install -r requirements.txt
```

### 3. Database Configuration
```bash
# Create PostgreSQL database
createdb insurance_tpa_db

# Update settings_integration.py with your database credentials
# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.postgresql',
#         'NAME': 'insurance_tpa_db',
#         'USER': 'your_db_user',
#         'PASSWORD': 'your_db_password',
#         'HOST': 'localhost',
#         'PORT': '5432',
#     }
# }
```

### 4. Generate Encryption Key
```bash
# Generate Fernet encryption key
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())" > encryption_key.key
chmod 600 encryption_key.key
```

### 5. Environment Configuration
```bash
# Create .env file
cp .env.example .env

# Update .env with your configuration
# ENCRYPTION_KEY_PATH=./encryption_key.key
# REDIS_URL=redis://localhost:6379/0
# CELERY_BROKER_URL=redis://localhost:6379/0
# DATABASE_URL=postgresql://user:password@localhost/insurance_tpa_db
# SECRET_KEY=your_django_secret_key
# DEBUG=True
```

### 6. Database Migrations
```bash
# Create and run migrations
python manage.py makemigrations insurance_tpa
python manage.py migrate

# Create superuser
python manage.py createsuperuser
```

## 🚀 Quick Start

### Development Environment (Docker Compose)
```bash
docker-compose up -d postgres redis

# In separate terminals:

# Terminal 1: Celery Worker
celery -A insurance_tpa worker --loglevel=info

# Terminal 2: Mock TPA Service
python -m insurance_tpa.mock_tpa

# Terminal 3: Django Server
python manage.py runserver 0.0.0.0:8000
```

### Manual Service Startup
```bash
# Terminal 1: Start Redis
redis-server --daemonize yes

# Terminal 2: Start PostgreSQL (if not using Docker)
systemctl start postgresql

# Terminal 3: Start Celery Worker
celery -A insurance_tpa worker --loglevel=info --concurrency=4

# Terminal 4: Start Mock TPA Service
python -m insurance_tpa.mock_tpa

# Terminal 5: Start Django Development Server
python manage.py runserver 0.0.0.0:8000
```

## 🔐 API Authentication

All endpoints require token-based authentication:

```bash
# Get authentication token
TOKEN=$(curl -X POST http://localhost:8000/api/v1/auth/token/ \
  -H "Content-Type: application/json" \
  -d '{"username": "your_username", "password": "your_password"}' | jq -r .token)

echo $TOKEN
```

## 📋 API Usage Examples

### 1. Create Pre-Authorization Request
```bash
curl -X POST http://localhost:8000/api/v1/insurance/pre-auth/create/ \
  -H "Authorization: Token $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "patient_id": "PAT12345678",
    "claim_amount": 50000.00,
    "procedures": ["Proc1", "Proc2"],
    "diagnosis": "Acute appendicitis"
  }'
```
**Response:**
```json
{
  "id": 1,
  "patient_id": "PAT12345678",
  "claim_amount": 50000.00,
  "status": "pending",
  "approval_id": null,
  "created_at": "2025-09-07T20:47:30Z"
}
```

### 2. List Pre-Authorizations
```bash
curl -X GET "http://localhost:8000/api/v1/insurance/pre-auth/?status=pending&page=1" \
  -H "Authorization: Token $TOKEN"
```
**Response:**
```json
{
  "count": 1,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": 1,
      "patient_id": "PAT12345678",
      "claim_amount": 50000.00,
      "status": "pending",
      "created_at": "2025-09-07T20:47:30Z"
    }
  ]
}
```

### 3. Create Insurance Claim
```bash
curl -X POST http://localhost:8000/api/v1/insurance/claims/create/ \
  -H "Authorization: Token $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "patient_id": "PAT12345678",
    "billed_amount": 45000.00,
    "procedures": ["Proc1", "Proc2", "Proc3"],
    "diagnosis": "Post-operative care",
    "preauth_id": 1
  }'
```
**Response:**
```json
{
  "id": 1,
  "patient_id": "PAT12345678",
  "billed_amount": 45000.00,
  "status": "pending",
  "claim_id": "CLM-20250907-001",
  "submitted_at": "2025-09-07T20:47:30Z"
}
```

### 4. Check Claim Status (Cached)
```bash
curl -X GET "http://localhost:8000/api/v1/insurance/claims/1/status/" \
  -H "Authorization: Token $TOKEN"
```
**Response:**
```json
{
  "claim_id": "CLM-20250907-001",
  "status": "approved",
  "processed_amount": 45000.00,
  "approval_date": "2025-09-07T21:02:15Z",
  "cached": true
}
```

### 5. Create Reimbursement
```bash
curl -X POST http://localhost:8000/api/v1/insurance/reimbursement/create/ \
  -H "Authorization: Token $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "claim_id": 1,
    "paid_amount": 40000.00,
    "transaction_id": "TXN-20250907-001",
    "payment_date": "2025-09-07"
  }'
```
**Response:**
```json
{
  "id": 1,
  "claim_id": 1,
  "paid_amount": 40000.00,
  "transaction_id": "TXN-20250907-001",
  "status": "paid",
  "processed_at": "2025-09-07T20:47:30Z"
}
```

## 🧪 Testing

### Run Unit and Integration Tests
```bash
# Install test dependencies
pip install pytest pytest-django pytest-cov factory-boy responses fakeredis

# Run tests with coverage
pytest tests/insurance_tpa/ --cov=insurance_tpa --cov-report=html --cov-fail-under=90 -v

# Generate coverage report
coverage html
open htmlcov/index.html  # View coverage report
```

### Run Mock TPA Tests
```bash
# Test Flask mock TPA service
pytest tests/insurance_tpa/test_mock_tpa.py -v
```

### Run Security Scans
```bash
# Pre-commit hooks
pre-commit install
pre-commit run --all-files

# Security vulnerability scan
bandit -r app/ -f html -o security-report.html
```

### Expected Test Results
- **Unit Tests**: 95%+ coverage
- **Integration Tests**: API endpoints, Celery tasks, Redis caching
- **Security Tests**: Encryption/decryption, SQL injection protection, XSS prevention
- **Performance Tests**: Rate limiting, concurrent request handling

## 🔧 Development

### Code Style
- **Python**: PEP 8 compliant (Black formatter)
- **Django**: Follows Django best practices
- **API**: RESTful design with JSON responses
- **Testing**: TDD approach with >90% coverage

### Pre-commit Hooks
```bash
# Install pre-commit hooks
pip install pre-commit
pre-commit install

# Available hooks:
# - black: Python code formatting
# - flake8: Python linting
# - isort: Import sorting
# - bandit: Security vulnerability scanning
# - mypy: Static type checking
```

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DEBUG` | Debug mode | `False` |
| `ENCRYPTION_KEY_PATH` | Path to Fernet key | `./encryption_key.key` |
| `REDIS_URL` | Redis connection URL | `redis://localhost:6379/0` |
| `CELERY_BROKER_URL` | Celery broker URL | `redis://localhost:6379/0` |
| `DATABASE_URL` | Database connection URL | `postgresql://user:pass@localhost/db` |
| `SECRET_KEY` | Django secret key | `django-insecure-...` |
| `TPA_MOCK_PORT` | Mock TPA service port | `5000` |
| `ALLOWED_HOSTS` | Django allowed hosts | `['*']` |

## 🐳 Docker Deployment

### Development Stack
```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

### Production Deployment
```bash
# Build and deploy
./deploy.sh

# Or using Docker Compose
ENV=production docker-compose up -d --build
```

**docker-compose.yml** services:
- **PostgreSQL**: Production database with connection pooling
- **Redis**: Caching and Celery broker
- **Django**: Gunicorn + Nginx reverse proxy
- **Celery**: Async task processing workers
- **Mock TPA**: Flask-based TPA simulation service
- **Prometheus**: Monitoring and metrics collection
- **Grafana**: Dashboard visualization

## 📊 Monitoring & Logging

### Structured Logging
All services use structured JSON logging:
```json
{
  "timestamp": "2025-09-07T20:47:30.123Z",
  "level": "INFO",
  "service": "insurance_tpa",
  "message": "Pre-auth request processed",
  "request_id": "req-123456789",
  "patient_id": "PAT12345678",
  "amount": 50000.00,
  "status": "approved"
}
```

### Key Metrics
- **API Response Time**: <200ms for cached responses
- **Task Processing Time**: <15s for TPA requests
- **Error Rate**: <0.1% for production traffic
- **Cache Hit Rate**: >80% for status polling
- **Database Query Time**: <50ms average

### Health Checks
```bash
# Django health check
curl http://localhost:8000/health/

# Mock TPA health check
curl http://localhost:5000/health

# Database connectivity
python manage.py check --deploy
```

## 🔒 Security

### Implemented Security Features
1. **Field-Level Encryption**: All financial data encrypted at rest using Fernet
2. **Rate Limiting**: Endpoint-specific throttling (5/min pre-auth, 3/min claims)
3. **Token Authentication**: Required for all API endpoints
4. **SQL Injection Protection**: Django ORM parameterization
5. **XSS Protection**: Input validation and output escaping
6. **CSRF Protection**: Django CSRF middleware enabled
7. **HTTPS Enforcement**: HSTS headers configured

### Security Testing
```bash
# Run security scans
bandit -r app/ -f json -o bandit-report.json
safety check

# SQL injection testing
pytest tests/insurance_tpa/test_views.py::TestClaimViews::test_claim_sql_injection_protection

# XSS protection testing
pytest tests/insurance_tpa/test_mock_tpa.py::TestSecurityAndEncryption::test_xss_protection
```

## 📚 Documentation

### API Documentation
- **OpenAPI Schema**: `schema.yaml` (generated with drf-spectacular)
- **Swagger UI**: Available at `/api/v1/schema/swagger-ui/` (development only)
- **ReDoc**: Available at `/api/v1/schema/redoc/`

### Architectural Decisions
- **ADR-001**: Financial Data Encryption Strategy (Fernet symmetric encryption)
- **ADR-002**: TPA Integration Architecture (Celery + Redis)
- **ADR-003**: Rate Limiting Strategy (DRF throttling)
- **ADR-004**: Data Retention Policy (365-day operational + 7-year audit)
- **ADR-005**: Mock TPA Service Architecture (Flask microservice)

### Database Schema
```sql
-- PreAuth table
CREATE TABLE insurance_tpa_preauth (
    id BIGSERIAL PRIMARY KEY,
    patient_id VARCHAR(50) NOT NULL,
    claim_amount_encrypted TEXT NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    approval_id VARCHAR(50),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX idx_preauth_status ON insurance_tpa_preauth(status);
CREATE INDEX idx_preauth_patient ON insurance_tpa_preauth(patient_id);
CREATE INDEX idx_preauth_created ON insurance_tpa_preauth(created_at);
```

## 🤝 Contributing

### Development Workflow
1. **Setup development environment** (see Installation above)
2. **Create feature branch**: `git checkout -b feature/new-endpoint`
3. **Write tests first** (TDD approach)
4. **Implement feature** with >90% test coverage
5. **Run pre-commit hooks**: `pre-commit run --all-files`
6. **Run full test suite**: `pytest --cov-fail-under=90`
7. **Push and create PR** with detailed description

### Code Review Checklist
- [ ] Tests pass with >90% coverage
- [ ] Pre-commit hooks pass
- [ ] Security scans clean (bandit)
- [ ] Documentation updated
- [ ] API responses properly validated
- [ ] Performance impact assessed
- [ ] Error handling implemented

### Commit Message Format
```
feat(insurance): add reimbursement endpoint with rate limiting

- Implement POST /api/v1/insurance/reimbursement/create/
- Add 2/min rate limiting
- Include encryption for paid_amount field
- Add comprehensive test coverage
- Update OpenAPI schema

Closes #123
```

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙌 Acknowledgments

- **Django REST Framework**: API framework foundation
- **Celery**: Async task processing
- **Redis**: Caching and message broker
- **PostgreSQL**: Robust relational database
- **drf-spectacular**: OpenAPI schema generation
- **pytest**: Comprehensive testing framework
- **factory-boy**: Test data generation

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/example/hms-enterprise/issues)
- **Discussions**: [GitHub Discussions](https://github.com/example/hms-enterprise/discussions)
- **Documentation**: [Project Wiki](https://github.com/example/hms-enterprise/wiki)
- **Email**: support@example.com

---

*Built with ❤️ for healthcare innovation*
