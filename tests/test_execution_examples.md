# Test Execution Examples

This document provides practical examples of how to use the comprehensive testing framework for the Enterprise-Grade HMS.

## Quick Start

### Running All Tests
```bash
# Run all test categories
python tests/run_tests.py --all

# Run all tests with verbose output
python tests/run_tests.py --all --verbose

# Run all tests and generate comprehensive report
python tests/run_tests.py --all --report
```

### Running Specific Test Categories
```bash
# Run unit tests only
python tests/run_tests.py --categories unit

# Run integration and e2e tests
python tests/run_tests.py --categories integration e2e

# Run security and compliance tests
python tests/run_tests.py --categories security compliance

# Run performance and accessibility tests
python tests/run_tests.py --categories performance accessibility
```

### Using pytest directly
```bash
# Run all tests with pytest
pytest

# Run specific test categories
pytest -m unit
pytest -m integration
pytest -m security
pytest -m compliance

# Run with coverage
pytest --cov=. --cov-report=html --cov-report=term-missing

# Run specific test files
pytest tests/unit/test_models_comprehensive.py
pytest tests/integration/test_api_endpoints_comprehensive.py
```

## Healthcare-Specific Testing

### HIPAA Compliance Testing
```bash
# Run HIPAA-specific compliance tests
pytest tests/compliance/test_compliance_comprehensive.py -m hipaa

# Run HIPAA security rule validation
pytest tests/security/test_security_comprehensive.py -m hipaa

# Run data encryption tests
pytest tests/unit/test_models_comprehensive.py::TestPatientModel::test_encryption
```

### GDPR Compliance Testing
```bash
# Run GDPR-specific compliance tests
pytest tests/compliance/test_compliance_comprehensive.py -m gdpr

# Test data portability
pytest tests/integration/test_api_endpoints_comprehensive.py::TestDataPortability

# Test right to be forgotten
pytest tests/e2e/test_healthcare_user_journeys.py::TestDataDeletion
```

### Accessibility Testing
```bash
# Run WCAG 2.1 compliance tests
pytest tests/accessibility/test_accessibility_comprehensive.py

# Run healthcare-specific accessibility tests
pytest tests/accessibility/test_accessibility_comprehensive.py -m healthcare

# Run screen reader compatibility tests
pytest tests/accessibility/test_accessibility_comprehensive.py -m screen_reader
```

## Performance Testing

### Load Testing
```bash
# Run performance tests
python tests/run_tests.py --categories performance

# Run specific load scenarios
pytest tests/performance/test_performance_comprehensive.py::TestLoadScenarios

# Run with custom configuration
pytest tests/performance/test_performance_comprehensive.py --performance-users=100 --performance-duration=300
```

### Stress Testing
```bash
# Run stress tests
pytest tests/performance/test_performance_comprehensive.py -m stress

# Run endurance tests
pytest tests/performance/test_performance_comprehensive.py -m endurance

# Run spike tests
pytest tests/performance/test_performance_comprehensive.py -m spike
```

## Security Testing

### OWASP Top 10 Testing
```bash
# Run comprehensive security scan
python tests/security/security_framework.py

# Run SQL injection tests
pytest tests/security/test_security_comprehensive.py -m sql_injection

# Run XSS tests
pytest tests/security/test_security_comprehensive.py -m xss

# Run authentication tests
pytest tests/security/test_security_comprehensive.py -m authentication
```

### Penetration Testing
```bash
# Run penetration testing suite
python tests/security/security_framework.py --penetration-test

# Run vulnerability assessment
python tests/security/security_framework.py --vulnerability-scan

# Run security audit
python tests/security/security_framework.py --security-audit
```

## Cross-Browser Testing

### Multi-Browser Testing
```bash
# Run cross-browser tests
python tests/run_tests.py --categories cross_browser

# Run specific browser tests
pytest tests/cross_browser/test_cross_browser_comprehensive.py -k chrome
pytest tests/cross_browser/test_cross_browser_comprehensive.py -k firefox
pytest tests/cross_browser/test_cross_browser_comprehensive.py -k safari

# Run mobile device tests
pytest tests/cross_browser/test_cross_browser_comprehensive.py -k mobile
pytest tests/cross_browser/test_cross_browser_comprehensive.py -k tablet
```

## Database Testing

### Migration Testing
```bash
# Run database migration tests
python tests/run_tests.py --categories database

# Test forward migration
pytest tests/database_migration/test_database_migration.py::TestDatabaseMigration::test_forward_migration

# Test backward migration
pytest tests/database_migration/test_database_migration.py::TestDatabaseMigration::test_backward_migration

# Test data integrity
pytest tests/database_migration/test_database_migration.py::TestDatabaseMigration::test_data_integrity
```

## End-to-End Testing

### Healthcare User Journeys
```bash
# Run patient registration journey
pytest tests/e2e/test_healthcare_user_journeys.py::TestPatientJourneys::test_patient_registration

# Run appointment scheduling journey
pytest tests/e2e/test_healthcare_user_journeys.py::TestAppointmentJourneys::test_appointment_scheduling

# Run medical records access journey
pytest tests/e2e/test_healthcare_user_journeys.py::TestMedicalRecordJourneys::test_medical_records_access

# Run billing workflow journey
pytest tests/e2e/test_healthcare_user_journeys.py::TestBillingJourneys::test_billing_workflow
```

## Test Data Management

### Generate Test Data
```bash
# Generate anonymized patient data
python tests/test_data/test_data_management.py --generate-patients --count=100

# Generate medical records
python tests/test_data/test_data_management.py --generate-medical-records --count=50

# Generate test data for all categories
python tests/test_data/test_data_management.py --generate-all

# Clean up test data
python tests/test_data/test_data_management.py --cleanup
```

## CI/CD Integration

### Local CI Execution
```bash
# Run CI pipeline locally
python tests/automation/ci_cd_integration.py --local

# Run GitHub Actions pipeline
python tests/automation/ci_cd_integration.py --platform github

# Run GitLab CI pipeline
python tests/automation/ci_cd_integration.py --platform gitlab

# Run Jenkins pipeline
python tests/automation/ci_cd_integration.py --platform jenkins
```

### Generate CI Configuration
```bash
# Generate GitHub Actions workflow
python tests/automation/ci_cd_integration.py --generate-config --platform github

# Generate GitLab CI configuration
python tests/automation/ci_cd_integration.py --generate-config --platform gitlab

# Generate Jenkins pipeline
python tests/automation/ci_cd_integration.py --generate-config --platform jenkins
```

## Test Reporting and Analysis

### Generate Test Reports
```bash
# Generate comprehensive test report
python tests/run_tests.py --all --report

# Generate coverage report
pytest --cov=. --cov-report=html --cov-report=term-missing

# Generate performance report
python tests/performance/test_performance_comprehensive.py --generate-report

# Generate security report
python tests/security/security_framework.py --generate-report
```

### Test Result Analysis
```bash
# Analyze test results
python tests/automation/test_automation_framework.py --analyze-results

# Generate performance trends
python tests/performance/test_performance_comprehensive.py --trends

# Generate compliance report
python tests/compliance/compliance_framework.py --generate-report
```

## Debugging and Troubleshooting

### Debug Failed Tests
```bash
# Run tests with debug output
pytest tests/unit/test_models_comprehensive.py --verbose --tb=long

# Run tests with pdb debugger
pytest tests/integration/test_api_endpoints_comprehensive.py --pdb

# Run tests with custom logging
pytest tests/security/test_security_comprehensive.py --log-level=DEBUG
```

### Environment Setup
```bash
# Setup test environment
python tests/run_tests.py --setup-only

# Check test environment
python tests/run_tests.py --list-categories

# Validate test configuration
python tests/conftest.py --validate
```

## Advanced Usage

### Parallel Test Execution
```bash
# Run tests in parallel with pytest-xdist
pytest -n auto

# Run tests with specific parallel workers
pytest -n 4

# Run tests with custom parallel configuration
pytest --dist=loadfile
```

### Custom Test Configuration
```bash
# Run tests with custom pytest.ini
pytest -c custom_pytest.ini

# Run tests with custom markers
pytest -m "custom_marker"

# Run tests with custom environment variables
TEST_ENVIRONMENT=staging pytest tests/integration/
```

### Performance Benchmarking
```bash
# Run performance benchmarks
python tests/performance/test_performance_comprehensive.py --benchmark

# Run baseline comparison
python tests/performance/test_performance_comprehensive.py --baseline

# Run performance regression tests
python tests/performance/test_performance_comprehensive.py --regression
```

## Continuous Testing

### Watch Mode
```bash
# Run tests in watch mode
pytest --watch

# Run specific tests in watch mode
pytest tests/unit/ --watch

# Run tests with custom watch configuration
pytest --watch --watch-extensions=py
```

### Pre-commit Hooks
```bash
# Run tests before commit
pytest tests/unit/ tests/integration/

# Run quick smoke tests
pytest -m smoke

# Run critical tests only
pytest tests/security/ tests/compliance/
```

## Best Practices

### Test Organization
1. **Run unit tests frequently** during development
2. **Run integration tests** before committing
3. **Run e2e tests** before deployment
4. **Run security tests** regularly
5. **Run compliance tests** before production releases

### Performance Considerations
1. **Run performance tests** during off-peak hours
2. **Monitor system resources** during performance testing
3. **Use test data caching** where appropriate
4. **Parallelize test execution** when possible

### Security Best Practices
1. **Never use real patient data** in tests
2. **Run security tests** in isolated environments
3. **Validate encryption** in all test scenarios
4. **Test audit trails** for completeness

### Compliance Requirements
1. **Run compliance tests** before each release
2. **Document test results** for audit purposes
3. **Maintain test coverage** above 95%
4. **Regularly update tests** for regulatory changes

## Getting Help

### Documentation
- Comprehensive test framework documentation: `tests/README.md`
- Pytest configuration: `tests/pytest.ini`
- Test execution examples: `tests/test_execution_examples.md`

### Support
- Test framework issues: Create issue in repository
- Configuration questions: Check documentation first
- Performance problems: Review test execution logs
- Security concerns: Contact security team

### Community
- Join our testing community for support and best practices
- Contribute to test framework improvements
- Share your testing experiences and solutions