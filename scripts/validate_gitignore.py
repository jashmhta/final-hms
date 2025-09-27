"""
validate_gitignore module
"""

import hashlib
import json
import os
import re
import subprocess
import sys
from dataclasses import asdict, dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple


class ValidationLevel(Enum):
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"
@dataclass
class ValidationResult:
    level: ValidationLevel
    message: str
    file_path: Optional[str] = None
    pattern: Optional[str] = None
    suggestion: Optional[str] = None
@dataclass
class GitignoreStats:
    total_lines: int
    comment_lines: int
    empty_lines: int
    pattern_lines: int
    file_size_bytes: int
    unique_patterns: int
    duplicate_patterns: int
class GitignoreValidator:
    def __init__(self, project_root: str = None):
        self.project_root = Path(project_root) if project_root else Path.cwd()
        self.gitignore_file = self.project_root / ".gitignore"
        self.validation_results: List[ValidationResult] = []
        self.stats: Optional[GitignoreStats] = None
        self.healthcare_patterns = {
            "patient_records", "patient_data", "phi_data", "protected_health_information",
            "medical_records", "health_records", "dicom_files", "medical_images",
            "xray_files", "mri_files", "ct_scans", "ultrasound_files", "*.dcm", "*.dicom",
            "device_data", "medical_device_data", "iot_device_data", "sensor_data",
            "vital_signs_data", "telemedicine_recordings", "consultation_recordings",
            "video_consultations", "audio_consultations", "research_data",
            "clinical_trials", "study_data", "participant_data"
        }
        self.sensitive_patterns = {
            "*.env", "*.key", "*.pem", "*.p12", "*.crt", "*.cert", "*.pfx", "*.keystore",
            "*.truststore", "*.jks", "*.csr", "secrets/", "credentials/", "*.password",
            "*.secret", "*.token", "*.jwt", "gpg_keys/", "pgp_keys/", "*.gpg", "*.pgp"
        }
        self.development_patterns = {
            "__pycache__", "*.pyc", "*.pyo", "*.pyd", "node_modules/", ".venv/",
            "venv/", "env/", "*.log", "*.tmp", "*.temp", ".cache/", "coverage/",
            ".pytest_cache/", ".mypy_cache/", ".idea/", ".vscode/", ".DS_Store", "Thumbs.db"
        }
    def add_result(self, level: ValidationLevel, message: str, **kwargs):
        result = ValidationResult(level=level, message=message, **kwargs)
        self.validation_results.append(result)
        print(f"[{level.value.upper()}] {message}")
    def validate_file_exists(self) -> bool:
        if not self.gitignore_file.exists():
            self.add_result(
                ValidationLevel.ERROR,
                f".gitignore file not found at {self.gitignore_file}"
            )
            return False
        self.add_result(ValidationLevel.INFO, f".gitignore file found at {self.gitignore_file}")
        return True
    def parse_gitignore(self) -> Tuple[List[str], List[str]]:
        if not self.gitignore_file.exists():
            return [], []
        patterns = []
        comments = []
        with open(self.gitignore_file, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue
                elif line.startswith('
                    comments.append((line_num, line))
                else:
                    patterns.append((line_num, line))
        return patterns, comments
    def calculate_stats(self) -> GitignoreStats:
        if not self.gitignore_file.exists():
            return GitignoreStats(0, 0, 0, 0, 0, 0, 0)
        patterns, comments = self.parse_gitignore()
        all_lines = patterns + comments
        pattern_list = [pattern for _, pattern in patterns]
        unique_patterns = set(pattern_list)
        duplicate_patterns = len(pattern_list) - len(unique_patterns)
        file_size = self.gitignore_file.stat().st_size
        return GitignoreStats(
            total_lines=len(all_lines),
            comment_lines=len(comments),
            empty_lines=0,  
            pattern_lines=len(patterns),
            file_size_bytes=file_size,
            unique_patterns=len(unique_patterns),
            duplicate_patterns=duplicate_patterns
        )
    def validate_syntax(self) -> bool:
        patterns, _ = self.parse_gitignore()
        syntax_issues = 0
        for line_num, pattern in patterns:
            if pattern.endswith('**'):
                self.add_result(
                    ValidationLevel.WARNING,
                    f"Pattern '{pattern}' (line {line_num}) ends with ** which might be too broad",
                    pattern=pattern,
                    suggestion="Consider if this broad pattern is intended"
                )
                syntax_issues += 1
            if pattern.startswith('/') and pattern.endswith('*'):
                self.add_result(
                    ValidationLevel.WARNING,
                    f"Pattern '{pattern}' (line {line_num}) starts with / and ends with *",
                    pattern=pattern,
                    suggestion="Consider if this specific pattern is intended"
                )
                syntax_issues += 1
            if re.search(r'[\[\]\(\)\{\}\^\$\|\?\*\+]', pattern) and not pattern.startswith('
                self.add_result(
                    ValidationLevel.INFO,
                    f"Pattern '{pattern}' (line {line_num}) contains regex characters",
                    pattern=pattern,
                    suggestion="Ensure regex patterns are intentional"
                )
        if syntax_issues == 0:
            self.add_result(ValidationLevel.INFO, "No syntax issues found")
        return syntax_issues == 0
    def validate_sensitive_files(self) -> bool:
        if not self.gitignore_file.exists():
            return False
        patterns, _ = self.parse_gitignore()
        pattern_set = {pattern for _, pattern in patterns}
        unignored_count = 0
        for sensitive_pattern in self.sensitive_patterns:
            if sensitive_pattern in pattern_set:
                self.add_result(ValidationLevel.INFO, f"Sensitive pattern '{sensitive_pattern}' is ignored")
            else:
                matching_files = list(self.project_root.rglob(sensitive_pattern.replace('*', '')))
                if matching_files:
                    self.add_result(
                        ValidationLevel.ERROR,
                        f"Sensitive pattern '{sensitive_pattern}' matches {len(matching_files)} files but is not ignored",
                        pattern=sensitive_pattern,
                        suggestion=f"Add '{sensitive_pattern}' to .gitignore"
                    )
                    unignored_count += 1
        return unignored_count == 0
    def validate_healthcare_compliance(self) -> bool:
        if not self.gitignore_file.exists():
            return False
        patterns, _ = self.parse_gitignore()
        pattern_set = {pattern for _, pattern in patterns}
        compliance_issues = 0
        for healthcare_pattern in self.healthcare_patterns:
            if healthcare_pattern not in pattern_set:
                self.add_result(
                    ValidationLevel.ERROR,
                    f"Healthcare pattern '{healthcare_pattern}' not found in .gitignore",
                    pattern=healthcare_pattern,
                    suggestion="Add healthcare-specific patterns for compliance"
                )
                compliance_issues += 1
        return compliance_issues == 0
    def validate_development_files(self) -> bool:
        if not self.gitignore_file.exists():
            return False
        patterns, _ = self.parse_gitignore()
        pattern_set = {pattern for _, pattern in patterns}
        missing_patterns = 0
        for dev_pattern in self.development_patterns:
            if dev_pattern not in pattern_set:
                self.add_result(
                    ValidationLevel.WARNING,
                    f"Development pattern '{dev_pattern}' not found in .gitignore",
                    pattern=dev_pattern,
                    suggestion="Consider adding common development patterns"
                )
                missing_patterns += 1
        return missing_patterns == 0
    def validate_tracked_files(self) -> bool:
        try:
            result = subprocess.run(
                ['git', 'ls-files'],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                check=True
            )
            tracked_files = result.stdout.strip().split('\n') if result.stdout.strip() else []
            problematic_files = 0
            for file_path in tracked_files:
                if not file_path:
                    continue
                if self._should_be_ignored(file_path):
                    self.add_result(
                        ValidationLevel.ERROR,
                        f"Tracked file '{file_path}' should be ignored",
                        file_path=file_path,
                        suggestion="Remove from repository or add to .gitignore"
                    )
                    problematic_files += 1
            return problematic_files == 0
        except subprocess.CalledProcessError:
            self.add_result(ValidationLevel.WARNING, "Could not validate tracked files - git command failed")
            return True
    def _should_be_ignored(self, file_path: str) -> bool:
        sensitive_extensions = {'.env', '.key', '.pem', '.p12', '.crt', '.cert', '.password', '.secret', '.token', '.jwt'}
        if any(file_path.endswith(ext) for ext in sensitive_extensions):
            return True
        try:
            result = subprocess.run(
                ['git', 'check-ignore', file_path],
                cwd=self.project_root,
                capture_output=True,
                text=True
            )
            return result.returncode == 0
        except subprocess.CalledProcessError:
            return False
    def check_ignored_files(self) -> bool:
        try:
            result = subprocess.run(
                ['git', 'ls-files', '--others', '--ignored', '--exclude-standard'],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                check=True
            )
            ignored_files = result.stdout.strip().split('\n') if result.stdout.strip() else []
            problematic_files = 0
            for file_path in ignored_files:
                if not file_path:
                    continue
                full_path = self.project_root / file_path
                if full_path.is_file():
                    file_size = full_path.stat().st_size
                    if file_size > 10 * 1024 * 1024:  
                        self.add_result(
                            ValidationLevel.WARNING,
                            f"Large ignored file: {file_path} ({file_size // (1024*1024)}MB)",
                            file_path=file_path
                        )
                        problematic_files += 1
                    if any(file_path.endswith(ext) for ext in ['.env', '.key', '.pem', '.password', '.secret']):
                        self.add_result(
                            ValidationLevel.WARNING,
                            f"Sensitive ignored file: {file_path}",
                            file_path=file_path
                        )
                        problematic_files += 1
            if problematic_files == 0:
                self.add_result(ValidationLevel.INFO, "No problematic ignored files found")
            return problematic_files == 0
        except subprocess.CalledProcessError:
            self.add_result(ValidationLevel.WARNING, "Could not check ignored files - git command failed")
            return True
    def validate_all(self) -> bool:
        print(f"Validating .gitignore for HMS Enterprise-Grade System")
        print(f"Project root: {self.project_root}")
        print(f".gitignore file: {self.gitignore_file}")
        print("-" * 60)
        self.stats = self.calculate_stats()
        checks = [
            self.validate_file_exists,
            self.validate_syntax,
            self.validate_sensitive_files,
            self.validate_healthcare_compliance,
            self.validate_development_files,
            self.validate_tracked_files,
            self.check_ignored_files
        ]
        failed_checks = 0
        for check in checks:
            if not check():
                failed_checks += 1
        print("\n" + "=" * 60)
        print("VALIDATION SUMMARY")
        print("=" * 60)
        if self.stats:
            print(f"Total lines: {self.stats.total_lines}")
            print(f"Pattern lines: {self.stats.pattern_lines}")
            print(f"Comment lines: {self.stats.comment_lines}")
            print(f"File size: {self.stats.file_size_bytes} bytes")
            print(f"Unique patterns: {self.stats.unique_patterns}")
            print(f"Duplicate patterns: {self.stats.duplicate_patterns}")
        print(f"\nFailed checks: {failed_checks}")
        error_count = sum(1 for r in self.validation_results if r.level == ValidationLevel.ERROR)
        warning_count = sum(1 for r in self.validation_results if r.level == ValidationLevel.WARNING)
        info_count = sum(1 for r in self.validation_results if r.level == ValidationLevel.INFO)
        print(f"Errors: {error_count}")
        print(f"Warnings: {warning_count}")
        print(f"Info: {info_count}")
        return failed_checks == 0 and error_count == 0
    def generate_report(self, output_format: str = "text") -> str:
        if output_format == "json":
            return self._generate_json_report()
        elif output_format == "html":
            return self._generate_html_report()
        else:
            return self._generate_text_report()
    def _generate_text_report(self) -> str:
        report = []
        report.append("HMS Enterprise-Grade System - .gitignore Validation Report")
        report.append("=" * 60)
        report.append(f"Generated: {datetime.now().isoformat()}")
        report.append(f"Project: {self.project_root}")
        report.append(f".gitignore: {self.gitignore_file}")
        report.append("")
        if self.stats:
            report.append("File Statistics:")
            report.append(f"  Total lines: {self.stats.total_lines}")
            report.append(f"  Pattern lines: {self.stats.pattern_lines}")
            report.append(f"  Comment lines: {self.stats.comment_lines}")
            report.append(f"  File size: {self.stats.file_size_bytes} bytes")
            report.append(f"  Unique patterns: {self.stats.unique_patterns}")
            report.append(f"  Duplicate patterns: {self.stats.duplicate_patterns}")
            report.append("")
        errors = [r for r in self.validation_results if r.level == ValidationLevel.ERROR]
        warnings = [r for r in self.validation_results if r.level == ValidationLevel.WARNING]
        infos = [r for r in self.validation_results if r.level == ValidationLevel.INFO]
        if errors:
            report.append("ERRORS:")
            for error in errors:
                report.append(f"  - {error.message}")
                if error.pattern:
                    report.append(f"    Pattern: {error.pattern}")
                if error.suggestion:
                    report.append(f"    Suggestion: {error.suggestion}")
            report.append("")
        if warnings:
            report.append("WARNINGS:")
            for warning in warnings:
                report.append(f"  - {warning.message}")
                if warning.pattern:
                    report.append(f"    Pattern: {warning.pattern}")
                if warning.suggestion:
                    report.append(f"    Suggestion: {warning.suggestion}")
            report.append("")
        if infos:
            report.append("INFO:")
            for info in infos[:10]:  
                report.append(f"  - {info.message}")
            if len(infos) > 10:
                report.append(f"  ... and {len(infos) - 10} more info messages")
            report.append("")
        report.append("RECOMMENDATIONS:")
        report.append("1. Review and address all ERROR level issues")
        report.append("2. Consider addressing WARNING level issues")
        report.append("3. Regularly validate .gitignore effectiveness")
        report.append("4. Document custom patterns for team reference")
        report.append("5. Integrate validation into CI/CD pipeline")
        return "\n".join(report)
    def _generate_json_report(self) -> str:
        report_data = {
            "timestamp": datetime.now().isoformat(),
            "project_root": str(self.project_root),
            "gitignore_file": str(self.gitignore_file),
            "stats": asdict(self.stats) if self.stats else None,
            "validation_results": [asdict(r) for r in self.validation_results],
            "summary": {
                "total": len(self.validation_results),
                "errors": sum(1 for r in self.validation_results if r.level == ValidationLevel.ERROR),
                "warnings": sum(1 for r in self.validation_results if r.level == ValidationLevel.WARNING),
                "info": sum(1 for r in self.validation_results if r.level == ValidationLevel.INFO)
            }
        }
        return json.dumps(report_data, indent=2)
    def _generate_html_report(self) -> str:
        html_template = 
        results_html = []
        for result in self.validation_results:
            css_class = f"{result.level.value}-result"
            html = f
            results_html.append(html)
        return html_template.format(
            timestamp=datetime.now().isoformat(),
            project_root=self.project_root,
            total_lines=self.stats.total_lines if self.stats else 0,
            pattern_lines=self.stats.pattern_lines if self.stats else 0,
            comment_lines=self.stats.comment_lines if self.stats else 0,
            file_size_bytes=self.stats.file_size_bytes if self.stats else 0,
            unique_patterns=self.stats.unique_patterns if self.stats else 0,
            duplicate_patterns=self.stats.duplicate_patterns if self.stats else 0,
            results_html='\n'.join(results_html)
        )
def main():
    import argparse
    parser = argparse.ArgumentParser(description="Validate .gitignore for HMS Enterprise-Grade System")
    parser.add_argument("--project-dir", help="Project directory")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose output")
    parser.add_argument("--report-only", action="store_true", help="Only generate report")
    parser.add_argument("--output-format", choices=["text", "json", "html"], default="text", help="Output format")
    args = parser.parse_args()
    validator = GitignoreValidator(args.project_dir)
    if args.report_only:
        report = validator.generate_report(args.output_format)
        print(report)
        return 0
    success = validator.validate_all()
    report = validator.generate_report(args.output_format)
    report_file = validator.project_root / "reports" / f"gitignore_validation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{args.output_format}"
    report_file.parent.mkdir(exist_ok=True)
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(report)
    print(f"\nReport saved to: {report_file}")
    return 0 if success else 1
if __name__ == "__main__":
    sys.exit(main())