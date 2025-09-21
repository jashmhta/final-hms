# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 🏥 HMS Enterprise-Grade System Overview

This is a comprehensive Healthcare Management System (HMS) built with Django + FastAPI backend and React frontend, featuring microservices architecture, enterprise-grade security, and healthcare compliance.

## 🔧 Common Development Commands

### Backend Development
```bash
# Main Django backend
cd backend && python manage.py runserver
cd backend && python manage.py migrate
cd backend && python manage.py createsuperuser
cd backend && python manage.py test
cd backend && python manage.py shell
cd backend && python manage.py loaddata [fixture]

# Individual service testing
cd services/[service_name] && python manage.py test
```

### Frontend Development
```bash
# React frontend
cd frontend && npm install
cd frontend && npm run dev
cd frontend && npm run build
cd frontend && npm run test
cd frontend && npm run lint
cd frontend && npm run type-check
```

### Docker Development
```bash
# Full stack development
make bootstrap              # Generate keys and start all services
make up                    # Start docker-compose stack
make down                  # Stop docker-compose stack
make logs                  # View logs
make seed                  # Seed demo data

# Individual service management
docker-compose up -d [service]
docker-compose logs -f [service]
```

### Testing Commands
```bash
# Backend testing
pytest -v                    # Run all tests
pytest -m unit               # Run unit tests only
pytest -m integration        # Run integration tests
pytest -m performance        # Run performance tests
pytest --cov=.               # Run with coverage

# Frontend testing
cd frontend && npm test
cd frontend && npm run test:coverage
cd frontend && npm run test:e2e
```

### Quality Assurance
```bash
# Code quality
make quality-analysis        # Run comprehensive quality analysis
make static-analysis         # Run static code analysis
make security-scan           # Run security scanning
make auto-fix               # Apply automatic fixes (black, isort)

# Individual tools
black .                      # Code formatting
isort .                     # Import sorting
flake8 .                    # Linting
mypy .                      # Type checking
bandit -r .                 # Security scanning
```

## 🏗️ Architecture Overview

### Backend Structure
- **Django Main App** (`backend/`): Core HMS application with 50+ Django apps
  - `hospitals/` - Hospital and facility management
  - `patients/` - Patient records and management
  - `ehr/` - Electronic Health Records
  - `pharmacy/` - Pharmacy and medication management
  - `lab/` - Laboratory results and management
  - `billing/` - Medical billing and insurance
  - `accounting/` - Financial accounting
  - `appointments/` - Appointment scheduling
  - `analytics/` - Business intelligence and analytics

- **Microservices** (`services/`): 40+ specialized services
  - `blood_bank/`, `radiology/`, `triage/`, `ambulance/`
  - `e_prescription/`, `consent/`, `audit/`
  - `backup_disaster_recovery/`, `cybersecurity_enhancements/`

### Frontend Structure
- **React Application** (`frontend/`): Modern React 18 + TypeScript
  - Material-UI components for healthcare UI
  - Redux Toolkit for state management
  - Recharts for medical data visualization

### Infrastructure
- **Containerization**: Docker + Kubernetes configurations
- **Monitoring**: Prometheus + Grafana + Jaeger
- **CI/CD**: GitHub Actions workflows
- **Database**: PostgreSQL with read replicas, Redis caching

## 🚨 Healthcare Compliance Requirements

### Security Standards
- **HIPAA Compliance**: All patient data must be encrypted at rest and in transit
- **GDPR Compliance**: Patient data privacy and right to be forgotten
- **PCI DSS**: Payment card processing security

### Data Handling
- **PHI (Protected Health Information)**: Must never be logged or exposed
- **Patient Privacy**: All patient data requires proper authentication
- **Audit Trails**: All access to patient data must be logged
- **Data Retention**: Follow healthcare data retention policies

### Code Standards
- **Security First**: Always validate inputs, sanitize outputs
- **Privacy by Design**: Minimize data collection, anonymize when possible
- **Defensive Programming**: Assume all external inputs are malicious
- **Error Handling**: Never expose sensitive information in error messages

## 📋 Development Patterns

### Backend Patterns
- **Django REST Framework**: Use ViewSets for REST APIs
- **FastAPI Integration**: High-performance services use FastAPI
- **Database Models**: Follow Django conventions, proper indexing
- **Authentication**: JWT-based with OAuth 2.0/OIDC support
- **Permissions**: Role-based access control (RBAC)

### Frontend Patterns
- **Component Architecture**: Reusable, composable components
- **State Management**: Redux Toolkit with RTK Query
- **Form Handling**: React Hook Form with validation
- **API Integration**: Axios with proper error handling
- **Styling**: Material-UI + custom Tailwind CSS

### Testing Requirements
- **Minimum Coverage**: 95% code coverage required
- **Test Categories**: Unit, Integration, E2E, Performance, Security
- **Healthcare-Specific Tests**: Patient data handling, privacy compliance
- **Mock Data**: Use anonymized test data, never real patient data

## 🎯 Key Development Principles

### Performance
- **Database Optimization**: Proper indexing, query optimization
- **Caching Strategy**: Redis for frequently accessed data
- **Async Processing**: Celery for background tasks
- **Frontend Optimization**: Code splitting, lazy loading

### Security
- **Input Validation**: Validate all inputs, never trust user data
- **SQL Injection Prevention**: Use Django ORM, never raw SQL
- **XSS Prevention**: Proper output escaping, CSP headers
- **CSRF Protection**: Django's built-in CSRF protection

### Maintainability
- **Code Organization**: Follow Django app structure
- **Documentation**: Comprehensive docstrings and comments
- **Error Handling**: Proper exception handling and logging
- **Version Control**: Semantic versioning, clear commit messages

## 🔧 Environment Setup

### Development Environment
```bash
# Clone and setup
git clone <repository>
cd enterprise-grade-hms
make setup-dev

# Environment variables
cp .env.example .env
# Edit .env with your configuration

# Database setup
createdb hms_enterprise_dev
python backend/manage.py migrate

# Start development servers
make up
```

### Testing Environment
```bash
# Run test suite
pytest

# Run specific test categories
pytest -m unit
pytest -m integration
pytest -m healthcare

# Performance testing
pytest -m performance
```

## 📚 Important Notes

### Healthcare Data Handling
- **NEVER** commit real patient data or PHI
- **ALWAYS** use anonymized test data
- **ENSURE** proper encryption for all sensitive data
- **MAINTAIN** audit trails for all data access

### Development Workflow
- **Feature Branches**: Create branches for new features
- **Code Reviews**: All code must be reviewed before merge
- **Testing**: All changes must pass automated tests
- **Documentation**: Update documentation for all changes

### Performance Considerations
- **Database Queries**: Optimize queries, use select_related/prefetch_related
- **Caching**: Implement caching for frequently accessed data
- **Frontend**: Optimize bundle size, implement lazy loading
- **APIs**: Use pagination, limit data transfer

## 🚫 Common Pitfalls to Avoid

### Security Issues
- **NEVER** hardcode credentials or sensitive data
- **NEVER** expose stack traces or detailed errors to users
- **NEVER** use GET requests for state-changing operations
- **NEVER** ignore security warnings or vulnerabilities

### Performance Issues
- **NEVER** use N+1 queries without optimization
- **NEVER** load all data without pagination
- **NEVER** ignore database indexes for frequent queries
- **NEVER** block the main thread with long operations

### Compliance Issues
- **NEVER** log sensitive patient information
- **NEVER** store unnecessary patient data
- **NEVER** ignore data retention policies
- **NEVER** bypass security controls for convenience