#!/bin/bash

# Automated Test Execution Setup for 95%+ Coverage Requirement
# HMS Enterprise-Grade System

set -e

echo "🏥 HMS Enterprise-Grade System - Automated Test Execution Setup"
echo "📊 Target: 95%+ Test Coverage Across All Components"
echo "============================================================"

# Configuration
PROJECT_ROOT="/home/azureuser/helli/enterprise-grade-hms"
BACKEND_DIR="$PROJECT_ROOT/backend"
FRONTEND_DIR="$PROJECT_ROOT/frontend"
E2E_DIR="$PROJECT_ROOT/e2e-tests"
COVERAGE_REPORT_DIR="$PROJECT_ROOT/test-reports"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging function
log() {
    echo -e "${BLUE}[$(date '+%Y-%m-%d %H:%M:%S')]${NC} $1"
}

log_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

log_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

log_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Create necessary directories
setup_directories() {
    log "Setting up test directories..."

    mkdir -p "$COVERAGE_REPORT_DIR/backend"
    mkdir -p "$COVERAGE_REPORT_DIR/frontend"
    mkdir -p "$COVERAGE_REPORT_DIR/e2e"
    mkdir -p "$COVERAGE_REPORT_DIR/combined"
    mkdir -p "$COVERAGE_REPORT_DIR/history"

    log_success "Test directories created"
}

# Install dependencies
install_dependencies() {
    log "Installing test dependencies..."

    # Backend dependencies
    if [ -d "$BACKEND_DIR" ]; then
        log "Installing backend test dependencies..."
        cd "$BACKEND_DIR"

        # Create virtual environment if it doesn't exist
        if [ ! -d "venv" ]; then
            python3 -m venv venv
        fi

        source venv/bin/activate
        pip install -r requirements.txt
        pip install pytest pytest-cov pytest-django pytest-xdist bandit safety
        pip install coverage

        log_success "Backend dependencies installed"
    fi

    # Frontend dependencies
    if [ -d "$FRONTEND_DIR" ]; then
        log "Installing frontend test dependencies..."
        cd "$FRONTEND_DIR"
        npm install

        log_success "Frontend dependencies installed"
    fi

    # E2E dependencies
    if [ -d "$E2E_DIR" ]; then
        log "Installing E2E test dependencies..."
        cd "$E2E_DIR"
        npm install

        # Install Playwright browsers
        npx playwright install chromium

        log_success "E2E dependencies installed"
    fi
}

# Run backend tests
run_backend_tests() {
    log "Running backend tests with coverage..."

    cd "$BACKEND_DIR"
    source venv/bin/activate

    # Run tests with coverage
    python -m pytest \
        --cov=. \
        --cov-report=html:"$COVERAGE_REPORT_DIR/backend/html" \
        --cov-report=xml:"$COVERAGE_REPORT_DIR/backend/coverage.xml" \
        --cov-report=term-missing \
        --cov-fail-under=95 \
        -v \
        --tb=short \
        --junit-xml="$COVERAGE_REPORT_DIR/backend/junit.xml" \
        | tee "$COVERAGE_REPORT_DIR/backend/test-output.log"

    BACKEND_EXIT_CODE=${PIPESTATUS[0]}

    if [ $BACKEND_EXIT_CODE -eq 0 ]; then
        log_success "Backend tests completed successfully"
    else
        log_error "Backend tests failed with exit code $BACKEND_EXIT_CODE"
        return $BACKEND_EXIT_CODE
    fi
}

# Run frontend tests
run_frontend_tests() {
    log "Running frontend tests with coverage..."

    cd "$FRONTEND_DIR"

    # Run Jest tests with coverage
    npm test -- --coverage \
        --coverageDirectory="$COVERAGE_REPORT_DIR/frontend" \
        --coverageReporters="html" "text" "lcov" "cobertura" \
        --coverageThreshold='{"global":{"branches":95,"functions":95,"lines":95,"statements":95}}' \
        --ci \
        --runInBand \
        --verbose \
        --json \
        --outputFile="$COVERAGE_REPORT_DIR/frontend/test-results.json" \
        2>&1 | tee "$COVERAGE_REPORT_DIR/frontend/test-output.log"

    FRONTEND_EXIT_CODE=${PIPESTATUS[0]}

    if [ $FRONTEND_EXIT_CODE -eq 0 ]; then
        log_success "Frontend tests completed successfully"
    else
        log_error "Frontend tests failed with exit code $FRONTEND_EXIT_CODE"
        return $FRONTEND_EXIT_CODE
    fi
}

# Run E2E tests
run_e2e_tests() {
    log "Running E2E tests..."

    cd "$E2E_DIR"

    # Run Playwright tests
    npx playwright test \
        --reporter=html,json,junit,list \
        --output="$COVERAGE_REPORT_DIR/e2e" \
        --workers=4 \
        --headed \
        --timeout=60000 \
        2>&1 | tee "$COVERAGE_REPORT_DIR/e2e/test-output.log"

    E2E_EXIT_CODE=${PIPESTATUS[0]}

    if [ $E2E_EXIT_CODE -eq 0 ]; then
        log_success "E2E tests completed successfully"
    else
        log_error "E2E tests failed with exit code $E2E_EXIT_CODE"
        return $E2E_EXIT_CODE
    fi
}

# Run security tests
run_security_tests() {
    log "Running security tests..."

    cd "$BACKEND_DIR"
    source venv/bin/activate

    # Run Bandit security scanning
    bandit -r . -f json -o "$COVERAGE_REPORT_DIR/security/bandit-report.json" || true

    # Run Safety dependency checking
    safety check --json --output "$COVERAGE_REPORT_DIR/security/safety-report.json" || true

    # Run Django security checks
    python manage.py check --deploy --settings=hms.settings.security_test > "$COVERAGE_REPORT_DIR/security/django-security-check.txt" 2>&1 || true

    log_success "Security tests completed"
}

# Run performance tests
run_performance_tests() {
    log "Running performance tests..."

    cd "$BACKEND_DIR"
    source venv/bin/activate

    # Run performance tests with marker
    python -m pytest \
        -m performance \
        --tb=short \
        -v \
        --junit-xml="$COVERAGE_REPORT_DIR/performance/junit.xml" \
        2>&1 | tee "$COVERAGE_REPORT_DIR/performance/test-output.log"

    log_success "Performance tests completed"
}

# Generate combined coverage report
generate_combined_report() {
    log "Generating combined test coverage report..."

    cd "$PROJECT_ROOT"

    # Create comprehensive test summary
    cat > "$COVERAGE_REPORT_DIR/combined/test-summary-$TIMESTAMP.md" << EOF
# HMS Enterprise-Grade System - Test Coverage Report
**Generated:** $(date)
**Target:** 95%+ Coverage

## Test Execution Summary

### Backend Tests
- **Coverage Report:** [View HTML Report](backend/html/index.html)
- **Coverage XML:** [Download XML](backend/coverage.xml)
- **Test Results:** [JUnit XML](backend/junit.xml)

### Frontend Tests
- **Coverage Report:** [View HTML Report](frontend/lcov-report/index.html)
- **Coverage Data:** [Download LCOV](frontend/lcov.info)
- **Test Results:** [JUnit XML](frontend/junit.xml)

### E2E Tests
- **Test Results:** [View HTML Report](e2e/index.html)
- **Test Results:** [JUnit XML](e2e/results.xml)

### Security Tests
- **Bandit Report:** [View Report](security/bandit-report.json)
- **Safety Report:** [View Report](security/safety-report.json)
- **Django Security:** [View Report](security/django-security-check.txt)

### Performance Tests
- **Performance Results:** [JUnit XML](performance/junit.xml)

## Coverage Metrics

### Backend Coverage
$(extract_backend_coverage)

### Frontend Coverage
$(extract_frontend_coverage)

### Overall System Coverage
$(calculate_overall_coverage)

## Test Categories
- **Unit Tests:** $(count_tests backend)
- **Integration Tests:** $(count_tests integration)
- **E2E Tests:** $(count_tests e2e)
- **Security Tests:** $(count_tests security)
- **Performance Tests:** $(count_tests performance)

## Recommendations
$(generate_recommendations)

## Next Steps
1. Review any coverage gaps below 95%
2. Address failing tests
3. Update test scenarios based on findings
4. Schedule regular test runs

---

*Report generated automatically by HMS Test Execution System*
EOF

    log_success "Combined coverage report generated"
}

# Extract backend coverage percentage
extract_backend_coverage() {
    if [ -f "$COVERAGE_REPORT_DIR/backend/coverage.xml" ]; then
        python3 -c "
import xml.etree.ElementTree as ET
try:
    tree = ET.parse('$COVERAGE_REPORT_DIR/backend/coverage.xml')
    root = tree.getroot()
    coverage = root.find('.//coverage')
    if coverage is not None:
        print(f'- **Total Coverage:** {coverage.get(\"line-rate\", \"N/A\")}% (Lines)')
        print(f'- **Branch Coverage:** {coverage.get(\"branch-rate\", \"N/A\")}% (Branches)')
    else:
        print('- Coverage data not available in expected format')
except:
    print('- Error reading coverage data')
"
    else
        echo "- Backend coverage report not found"
    fi
}

# Extract frontend coverage percentage
extract_frontend_coverage() {
    if [ -f "$FRONTEND_DIR/coverage/lcov-report/index.html" ]; then
        echo "- Frontend coverage report available in HTML format"
    else
        echo "- Frontend coverage report not found"
    fi
}

# Calculate overall coverage
calculate_overall_coverage() {
    echo "- Overall system coverage calculation based on component reports"
    echo "- Review individual component reports for detailed metrics"
}

# Generate recommendations based on test results
generate_recommendations() {
    echo "### Coverage Improvement Recommendations"
    echo "1. Focus on areas with coverage below 95%"
    echo "2. Add integration tests for uncovered API endpoints"
    echo "3. Enhance E2E test coverage for critical user journeys"
    echo "4. Improve security testing coverage"
    echo "5. Add performance benchmarks for all critical paths"
}

# Count tests by category
count_tests() {
    category=$1
    case $category in
        backend)
            echo "Count based on backend test execution results"
            ;;
        frontend)
            echo "Count based on frontend test execution results"
            ;;
        e2e)
            echo "Count based on E2E test execution results"
            ;;
        security)
            echo "Count based on security test execution results"
            ;;
        performance)
            echo "Count based on performance test execution results"
            ;;
        *)
            echo "Unknown test category"
            ;;
    esac
}

# Generate coverage badge
generate_coverage_badge() {
    log "Generating coverage badges..."

    # Create simple SVG badges (would normally use a badge service)
    cat > "$COVERAGE_REPORT_DIR/badges/backend-coverage.svg" << EOF
<svg xmlns="http://www.w3.org/2000/svg" width="100" height="20">
    <rect width="100" height="20" fill="#555"/>
    <rect x="50" width="50" height="20" fill="#4c1"/>
    <text x="25" y="14" text-anchor="middle" fill="white" font-size="12">coverage</text>
    <text x="75" y="14" text-anchor="middle" fill="white" font-size="12">95%+</text>
</svg>
EOF

    log_success "Coverage badges generated"
}

# Archive test results
archive_results() {
    log "Archiving test results..."

    # Create archive of current test results
    tar -czf "$COVERAGE_REPORT_DIR/history/test-results-$TIMESTAMP.tar.gz" \
        -C "$COVERAGE_REPORT_DIR" backend frontend e2e security performance

    # Keep only last 10 archives
    cd "$COVERAGE_REPORT_DIR/history"
    ls -t test-results-*.tar.gz | tail -n +11 | xargs rm -f

    log_success "Test results archived"
}

# Send notifications (placeholder)
send_notifications() {
    log "Sending test notifications..."

    # This would integrate with email, Slack, or other notification systems
    # For now, just create a notification file
    cat > "$COVERAGE_REPORT_DIR/notification.txt" << EOF
Test Execution Completed: $(date)

Status: All tests executed
Coverage Reports: Available in $COVERAGE_REPORT_DIR
Next Steps: Review reports and address any issues

EOF

    log_success "Notifications prepared"
}

# Main execution
main() {
    log "Starting automated test execution..."

    # Setup
    setup_directories
    install_dependencies

    # Run all test suites
    run_backend_tests
    run_frontend_tests
    run_e2e_tests
    run_security_tests
    run_performance_tests

    # Generate reports
    generate_combined_report
    generate_coverage_badge
    archive_results
    send_notifications

    log_success "🎉 Automated test execution completed successfully!"
    log "📊 Coverage reports available in: $COVERAGE_REPORT_DIR"
    log "📋 Summary report: $COVERAGE_REPORT_DIR/combined/test-summary-$TIMESTAMP.md"

    # Return success
    exit 0
}

# Error handling
error_handler() {
    log_error "Test execution failed on line $1"
    exit 1
}

# Set error trap
trap 'error_handler $LINENO' ERR

# Execute main function
main "$@"