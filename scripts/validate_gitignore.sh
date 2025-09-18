#!/bin/bash
set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
GITIGNORE_FILE="$PROJECT_ROOT/.gitignore"
VALIDATION_LOG="$PROJECT_ROOT/logs/gitignore_validation.log"
COMPLIANCE_REPORT="$PROJECT_ROOT/reports/gitignore_compliance_report.txt"
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' 
log_message() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$VALIDATION_LOG"
}
log_error() {
    echo -e "${RED}[ERROR]${NC} $1" | tee -a "$VALIDATION_LOG"
}
log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1" | tee -a "$VALIDATION_LOG"
}
log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1" | tee -a "$VALIDATION_LOG"
}
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1" | tee -a "$VALIDATION_LOG"
}
check_gitignore_exists() {
    log_info "Checking if .gitignore file exists..."
    if [[ ! -f "$GITIGNORE_FILE" ]]; then
        log_error ".gitignore file not found at $GITIGNORE_FILE"
        return 1
    fi
    log_success ".gitignore file found"
    return 0
}
check_gitignore_syntax() {
    log_info "Validating .gitignore syntax..."
    local syntax_issues=0
    while IFS= read -r pattern; do
        [[ "$pattern" =~ ^[[:space:]]*
        [[ -z "$pattern" ]] && continue
        if [[ "$pattern" =~ \*\*$ ]]; then
            log_warning "Pattern '$pattern' ends with ** which might be too broad"
            ((syntax_issues++))
        fi
        if [[ "$pattern" =~ ^/.*\*$ ]]; then
            log_warning "Pattern '$pattern' starts with / and ends with * - consider if this is intended"
            ((syntax_issues++))
        fi
    done < "$GITIGNORE_FILE"
    if [[ $syntax_issues -gt 0 ]]; then
        log_warning "Found $syntax_issues potential syntax issues in .gitignore"
    else
        log_success ".gitignore syntax validation passed"
    fi
}
check_sensitive_files_ignored() {
    log_info "Checking for sensitive files that should be ignored..."
    local sensitive_patterns=(
        "*.env"
        "*.key"
        "*.pem"
        "*.p12"
        "*.crt"
        "*.cert"
        "secrets/"
        "credentials/"
        "*.password"
        "*.secret"
        "*.token"
        "*.jwt"
        "patient_data/"
        "phi_data/"
        "medical_records/"
        "dicom_files/"
        "*.dcm"
        "*.dicom"
        "device_data/"
        "research_data/"
        "clinical_trials/"
    )
    local unignored_files=0
    for pattern in "${sensitive_patterns[@]}"; do
        if git check-ignore "$pattern" >/dev/null 2>&1; then
            log_success "Pattern '$pattern' is properly ignored"
        else
            local matches=$(find "$PROJECT_ROOT" -name "$pattern" -type f 2>/dev/null | head -5)
            if [[ -n "$matches" ]]; then
                log_error "Pattern '$pattern' matches existing files but is not ignored"
                echo "$matches" | while read -r file; do
                    log_error "  - $file"
                done
                ((unignored_files++))
            fi
        fi
    done
    if [[ $unignored_files -gt 0 ]]; then
        log_error "Found $unignored_files sensitive file types not properly ignored"
        return 1
    else
        log_success "All sensitive file patterns are properly ignored"
        return 0
    fi
}
check_ignored_files_exist() {
    log_info "Checking if ignored files actually exist in repository..."
    local ignored_files=$(git ls-files --others --ignored --exclude-standard 2>/dev/null || true)
    if [[ -z "$ignored_files" ]]; then
        log_info "No ignored files found in working directory"
        return 0
    fi
    local ignored_count=$(echo "$ignored_files" | wc -l)
    log_info "Found $ignored_count ignored files in working directory"
    local problematic_files=0
    echo "$ignored_files" | while read -r file; do
        if [[ -n "$file" ]]; then
            if [[ -f "$file" ]]; then
                local file_size=$(stat -c%s "$file" 2>/dev/null || echo 0)
                if [[ $file_size -gt 10485760 ]]; then  
                    log_warning "Large ignored file: $file ($((file_size / 1024 / 1024))MB)"
                    ((problematic_files++))
                fi
            fi
            if [[ "$file" =~ \.(env|key|pem|p12|crt|cert|password|secret|token|jwt)$ ]]; then
                log_warning "Sensitive ignored file: $file"
                ((problematic_files++))
            fi
        fi
    done
    if [[ $problematic_files -gt 0 ]]; then
        log_warning "Found $problematic_files potentially problematic ignored files"
    else
        log_success "Ignored files validation passed"
    fi
}
check_tracked_files_should_be_ignored() {
    log_info "Checking if tracked files should be ignored..."
    local problematic_files=0
    git ls-files | while read -r file; do
        if git check-ignore "$file" >/dev/null 2>&1; then
            log_error "Tracked file '$file' matches .gitignore pattern but is tracked"
            ((problematic_files++))
        fi
        if [[ "$file" =~ \.(env|key|pem|p12|crt|cert|password|secret|token|jwt)$ ]]; then
            log_error "Tracked sensitive file: $file"
            ((problematic_files++))
        fi
    done
    if [[ $problematic_files -gt 0 ]]; then
        log_error "Found $problematic_files tracked files that should be ignored"
        return 1
    else
        log_success "No tracked files should be ignored"
        return 0
    fi
}
check_healthcare_compliance() {
    log_info "Checking healthcare-specific compliance..."
    local compliance_patterns=(
        "patient_records"
        "patient_data"
        "phi_data"
        "protected_health_information"
        "medical_records"
        "health_records"
        "dicom_files"
        "medical_images"
        "xray_files"
        "mri_files"
        "ct_scans"
        "ultrasound_files"
        "device_data"
        "medical_device_data"
        "iot_device_data"
        "sensor_data"
        "vital_signs_data"
        "telemedicine_recordings"
        "consultation_recordings"
        "video_consultations"
        "audio_consultations"
        "research_data"
        "clinical_trials"
        "study_data"
        "participant_data"
    )
    local compliance_issues=0
    for pattern in "${compliance_patterns[@]}"; do
        if ! grep -q "^$pattern" "$GITIGNORE_FILE"; then
            log_error "Healthcare compliance pattern '$pattern' not found in .gitignore"
            ((compliance_issues++))
        fi
    done
    local file_extensions=("\*.dcm" "\*.dicom")
    for ext in "${file_extensions[@]}"; do
        if ! grep -q "^$ext" "$GITIGNORE_FILE"; then
            log_error "Healthcare file extension '$ext' not found in .gitignore"
            ((compliance_issues++))
        fi
    done
    if [[ $compliance_issues -gt 0 ]]; then
        log_error "Found $compliance_issues healthcare compliance issues"
        return 1
    else
        log_success "Healthcare compliance validation passed"
        return 0
    fi
}
check_common_development_files() {
    log_info "Checking common development files are ignored..."
    local dev_patterns=(
        "__pycache__"
        "*.pyc"
        "*.pyo"
        "*.pyd"
        "node_modules/"
        ".venv/"
        "venv/"
        "env/"
        "*.log"
        "*.tmp"
        "*.temp"
        ".cache/"
        "coverage/"
        ".pytest_cache/"
        ".mypy_cache/"
        ".idea/"
        ".vscode/"
        ".DS_Store"
        "Thumbs.db"
    )
    local missing_patterns=0
    for pattern in "${dev_patterns[@]}"; do
        if ! grep -q "^$pattern" "$GITIGNORE_FILE"; then
            log_warning "Common development pattern '$pattern' not found in .gitignore"
            ((missing_patterns++))
        fi
    done
    if [[ $missing_patterns -gt 0 ]]; then
        log_warning "Found $missing_patterns missing common development patterns"
    else
        log_success "Common development files validation passed"
    fi
}
check_gitignore_size() {
    log_info "Checking .gitignore file size..."
    local line_count=$(wc -l < "$GITIGNORE_FILE")
    local file_size=$(stat -c%s "$GITIGNORE_FILE" 2>/dev/null || echo 0)
    log_info ".gitignore has $line_count lines and is $file_size bytes"
    if [[ $line_count -lt 50 ]]; then
        log_warning ".gitignore seems small ($line_count lines) - may be incomplete"
    elif [[ $line_count -gt 1000 ]]; then
        log_warning ".gitignore is large ($line_count lines) - consider optimization"
    else
        log_success ".gitignore size is appropriate"
    fi
}
check_duplicate_patterns() {
    log_info "Checking for duplicate patterns in .gitignore..."
    local duplicates=$(sort "$GITIGNORE_FILE" | grep -v "^
    if [[ -n "$duplicates" ]]; then
        log_warning "Found duplicate patterns in .gitignore:"
        echo "$duplicates" | while read -r pattern; do
            log_warning "  - $pattern"
        done
    else
        log_success "No duplicate patterns found"
    fi
}
generate_compliance_report() {
    log_info "Generating compliance report..."
    mkdir -p "$(dirname "$COMPLIANCE_REPORT")"
    {
        echo "HMS Enterprise-Grade System - .gitignore Compliance Report"
        echo "============================================================"
        echo "Generated: $(date)"
        echo ""
        echo "
        echo "- Location: $GITIGNORE_FILE"
        echo "- Size: $(stat -c%s "$GITIGNORE_FILE" 2>/dev/null || echo 0) bytes"
        echo "- Lines: $(wc -l < "$GITIGNORE_FILE" 2>/dev/null || echo 0)"
        echo ""
        echo "
        echo "- .gitignore exists: $([[ -f "$GITIGNORE_FILE" ]] && echo "✓" || echo "✗")"
        echo "- Sensitive files ignored: $([[ $(check_sensitive_files_ignored 2>/dev/null; echo $?) -eq 0 ]] && echo "✓" || echo "✗")"
        echo "- Healthcare compliance: $([[ $(check_healthcare_compliance 2>/dev/null; echo $?) -eq 0 ]] && echo "✓" || echo "✗")"
        echo "- Common development files: $([[ $(check_common_development_files 2>/dev/null; echo $?) -eq 0 ]] && echo "✓" || echo "✗")"
        echo ""
        echo "
        echo "- Total patterns: $(grep -v "^
        echo "- Comment lines: $(grep "^
        echo "- Empty lines: $(grep "^$" "$GITIGNORE_FILE" | wc -l)"
        echo ""
        echo "
        grep -v "^
        while read -r count pattern; do
            echo "- $pattern: $count occurrences"
        done
        echo ""
        echo "
        echo "1. Regularly review and update .gitignore as project evolves"
        echo "2. Test .gitignore effectiveness after major changes"
        echo "3. Document any custom patterns for team reference"
        echo "4. Consider using .gitignore templates for consistency"
        echo "5. Validate .gitignore in CI/CD pipeline"
        echo ""
        echo "
        echo "1. Address any issues identified in this report"
        echo "2. Schedule regular .gitignore reviews"
        echo "3. Integrate validation into development workflow"
        echo "4. Educate team on .gitignore best practices"
    } > "$COMPLIANCE_REPORT"
    log_success "Compliance report generated: $COMPLIANCE_REPORT"
}
main() {
    log_info "Starting .gitignore validation for HMS Enterprise-Grade System"
    log_info "Project root: $PROJECT_ROOT"
    log_info ".gitignore file: $GITIGNORE_FILE"
    log_info ""
    mkdir -p "$(dirname "$VALIDATION_LOG")"
    local failed_checks=0
    check_gitignore_exists || ((failed_checks++))
    check_gitignore_syntax || ((failed_checks++))
    check_sensitive_files_ignored || ((failed_checks++))
    check_ignored_files_exist || ((failed_checks++))
    check_tracked_files_should_be_ignored || ((failed_checks++))
    check_healthcare_compliance || ((failed_checks++))
    check_common_development_files || ((failed_checks++))
    check_gitignore_size || ((failed_checks++))
    check_duplicate_patterns || ((failed_checks++))
    generate_compliance_report
    log_info ""
    log_info "Validation Summary"
    log_info "================"
    if [[ $failed_checks -eq 0 ]]; then
        log_success "All validation checks passed!"
        log_success ".gitignore configuration is effective and compliant"
        exit 0
    else
        log_error "Failed validation checks: $failed_checks"
        log_error "Please review and fix the issues identified above"
        log_error "Check the validation log: $VALIDATION_LOG"
        log_error "Check the compliance report: $COMPLIANCE_REPORT"
        exit 1
    fi
}
while [[ $
    case $1 in
        --help|-h)
            echo "HMS Enterprise-Grade .gitignore Validation Script"
            echo ""
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --help, -h     Show this help message"
            echo "  --project-dir  Specify project directory (default: auto-detect)"
            echo "  --verbose      Enable verbose output"
            echo "  --report-only  Only generate report, skip validation"
            echo ""
            exit 0
            ;;
        --project-dir)
            PROJECT_ROOT="$2"
            shift 2
            ;;
        --verbose)
            set -x
            shift
            ;;
        --report-only)
            generate_compliance_report
            exit 0
            ;;
        *)
            log_error "Unknown option: $1"
            exit 1
            ;;
    esac
done
main "$@"