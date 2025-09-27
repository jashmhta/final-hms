"""
Comprehensive Input Validation and XSS Prevention for Healthcare Data
Implements strict validation for all healthcare-related inputs
"""

import html
import json
import re
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union
from urllib.parse import urlparse

from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator, validate_email
from django.utils.html import strip_tags
from django.utils.translation import gettext_lazy as _

from .encryption import healthcare_encryption


class HealthcareDataValidator:
    """
    Validator for healthcare-specific data with HIPAA compliance requirements
    """

    # Regex patterns for healthcare data validation
    PATTERNS = {
        "medical_record_number": r"^[A-Z0-9]{2,20}$",
        "ssn": r"^\d{3}-?\d{2}-?\d{4}$",
        "phone_us": r"^\+?1?[-.\s]?\(?[0-9]{3}\)?[-.\s]?[0-9]{3}[-.\s]?[0-9]{4}$",
        "phone_international": r"^\+[0-9]{1,3}[-.\s]?[0-9]{4,14}$",
        "zip_code_us": r"^\d{5}(-?\d{4})?$",
        "date_iso": r"^\d{4}-\d{2}-\d{2}$",
        "time_iso": r"^\d{2}:\d{2}:\d{2}$",
        "datetime_iso": r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})?$",
        "diagnosis_code": r"^[A-Z][0-9]{2}(\.[0-9]{1,2})?$|^V[0-9]{2}(\.[0-9]{1,2})?$|^E[0-9]{3}(\.[0-9]{1,2})?$",
        "procedure_code": r"^\d{4,5}$|^[0-9]{4}[A-Z][0-9]{2}$",
        "ndc_code": r"^\d{4,5}-\d{4}-\d{2}$|^\d{10}$",
        "loinc_code": r"^[0-9]{1,5}-[0-9]$",
        "snomed_code": r"^[0-9]{6,18}$",
        "allergy_severity": r"^(Mild|Moderate|Severe|Life-threatening)$",
        "blood_type": r"^(A|B|AB|O)[+-]$",
        "medication_dosage": r"^\d+(?:\.\d+)?\s*(mg|g|mcg|ml|cc|units|IU|mEq)?$",
        "vital_sign_value": r"^\d+(?:\.\d+)?$",
        "height_us": r"^\d{1,2}\'\s*\d{1,2}?$|^(\d+(?:\.\d+)?)\s*(cm|in)$",
        "weight_us": r"^\d+(?:\.\d+)?\s*(lb|lbs|kg|oz)$",
        "temperature": r"^\d+(?:\.\d+)?\s*(F|C)$",
        "pressure": r"^\d{2,3}/\d{2,3}$",
        "pulse": r"^\d{1,3}\s*(bpm)?$",
        "oxygen_saturation": r"^\d{1,3}\s*%?$",
        "glucose": r"^\d+(?:\.\d+)?\s*(mg/dL|mmol/L)$",
    }

    # Field length restrictions for healthcare data
    MAX_LENGTHS = {
        "first_name": 50,
        "last_name": 50,
        "middle_name": 50,
        "email": 100,
        "phone": 20,
        "address_line1": 100,
        "address_line2": 100,
        "city": 50,
        "state": 50,
        "country": 50,
        "zip_code": 20,
        "medical_record_number": 20,
        "diagnosis": 500,
        "medication_name": 100,
        "allergen": 100,
        "provider_notes": 2000,
        "lab_result_value": 100,
        "vital_notes": 200,
    }

    def __init__(self):
        self.xss_cleaner = XSSCleaner()

    def validate_patient_data(self, data: Dict) -> Dict[str, List[str]]:
        """
        Validate patient data with healthcare-specific rules
        Returns dictionary of validation errors
        """
        errors = {}

        # Required fields validation
        required_fields = [
            "first_name",
            "last_name",
            "date_of_birth",
            "gender",
            "contact_method",
        ]
        for field in required_fields:
            if field not in data or not data[field]:
                errors[field] = [_("This field is required")]

        # Field-specific validation
        if "first_name" in data:
            errors.update(self._validate_name(data["first_name"], "first_name"))
        if "last_name" in data:
            errors.update(self._validate_name(data["last_name"], "last_name"))
        if "email" in data and data["email"]:
            errors.update(self._validate_email(data["email"]))
        if "phone" in data:
            errors.update(self._validate_phone(data["phone"]))
        if "date_of_birth" in data:
            errors.update(self._validate_date_of_birth(data["date_of_birth"]))
        if "ssn" in data and data["ssn"]:
            errors.update(self._validate_ssn(data["ssn"]))
        if "medical_record_number" in data:
            errors.update(
                self._validate_medical_record_number(data["medical_record_number"])
            )

        # Sanitize all string fields
        sanitized_data = self._sanitize_dict(data)

        return errors

    def validate_medication_data(self, data: Dict) -> Dict[str, List[str]]:
        """Validate medication-related data"""
        errors = {}

        if "name" not in data or not data["name"]:
            errors["name"] = [_("Medication name is required")]

        if "dosage" in data:
            errors.update(self._validate_dosage(data["dosage"]))

        if "ndc_code" in data and data["ndc_code"]:
            errors.update(self._validate_ndc_code(data["ndc_code"]))

        if "instructions" in data:
            errors.update(self._validate_instructions(data["instructions"]))

        return errors

    def validate_lab_result(self, data: Dict) -> Dict[str, List[str]]:
        """Validate laboratory result data"""
        errors = {}

        if "test_code" not in data or not data["test_code"]:
            errors["test_code"] = [_("Test code is required")]

        if "value" in data:
            errors.update(self._validate_lab_value(data["value"], data.get("unit")))

        if "reference_range" in data:
            errors.update(self._validate_reference_range(data["reference_range"]))

        return errors

    def _validate_name(self, value: str, field_name: str) -> Dict[str, List[str]]:
        """Validate name fields"""
        errors = {}
        if not isinstance(value, str):
            errors[field_name] = [_("Invalid name format")]
            return errors

        # Check length
        if len(value) > self.MAX_LENGTHS.get(field_name, 50):
            errors[field_name] = [_("Name is too long")]

        # Check for invalid characters
        if not re.match(r"^[A-Za-zÀ-ÿ\s\'-]+$", value):
            errors[field_name] = [_("Name contains invalid characters")]

        return errors

    def _validate_email(self, email: str) -> Dict[str, List[str]]:
        """Validate email with additional checks"""
        errors = {}
        try:
            validate_email(email)
            # Additional validation for healthcare emails
            if len(email) > self.MAX_LENGTHS["email"]:
                errors["email"] = [_("Email is too long")]
            # Check for disposable email domains (simplified)
            disposable_domains = ["tempmail.com", "10minutemail.com"]
            domain = email.split("@")[1].lower()
            if domain in disposable_domains:
                errors["email"] = [_("Disposable email domains are not allowed")]
        except ValidationError:
            errors["email"] = [_("Invalid email format")]
        return errors

    def _validate_phone(self, phone: str) -> Dict[str, List[str]]:
        """Validate phone number (US or international)"""
        errors = {}
        if not re.match(self.PATTERNS["phone_us"], phone) and not re.match(
            self.PATTERNS["phone_international"], phone
        ):
            errors["phone"] = [_("Invalid phone number format")]
        return errors

    def _validate_date_of_birth(self, dob: str) -> Dict[str, List[str]]:
        """Validate date of birth"""
        errors = {}
        try:
            if not re.match(self.PATTERNS["date_iso"], dob):
                errors["date_of_birth"] = [_("Invalid date format. Use YYYY-MM-DD")]
                return errors

            dob_date = datetime.strptime(dob, "%Y-%m-%d").date()
            today = datetime.now().date()

            # Check reasonable age range
            age = (today - dob_date).days / 365.25
            if age < 0 or age > 150:
                errors["date_of_birth"] = [_("Invalid date of birth")]
        except ValueError:
            errors["date_of_birth"] = [_("Invalid date format")]
        return errors

    def _validate_ssn(self, ssn: str) -> Dict[str, List[str]]:
        """Validate SSN with HIPAA compliance"""
        errors = {}
        if not re.match(self.PATTERNS["ssn"], ssn):
            errors["ssn"] = [_("Invalid SSN format")]
        # Additional validation for invalid SSN patterns
        clean_ssn = ssn.replace("-", "")
        if clean_ssn in ["000000000", "111111111", "123456789"]:
            errors["ssn"] = [_("Invalid SSN")]
        return errors

    def _validate_medical_record_number(self, mrn: str) -> Dict[str, List[str]]:
        """Validate medical record number"""
        errors = {}
        if not re.match(self.PATTERNS["medical_record_number"], mrn):
            errors["medical_record_number"] = [
                _("Invalid medical record number format")
            ]
        return errors

    def _validate_dosage(self, dosage: str) -> Dict[str, List[str]]:
        """Validate medication dosage"""
        errors = {}
        if not re.match(self.PATTERNS["medication_dosage"], dosage):
            errors["dosage"] = [_("Invalid dosage format")]
        return errors

    def _validate_ndc_code(self, ndc: str) -> Dict[str, List[str]]:
        """Validate NDC code"""
        errors = {}
        if not re.match(self.PATTERNS["ndc_code"], ndc):
            errors["ndc_code"] = [_("Invalid NDC code format")]
        return errors

    def _validate_instructions(self, instructions: str) -> Dict[str, List[str]]:
        """Validate medication instructions"""
        errors = {}
        if len(instructions) > 500:
            errors["instructions"] = [_("Instructions too long")]
        return errors

    def _validate_lab_value(
        self, value: str, unit: Optional[str]
    ) -> Dict[str, List[str]]:
        """Validate lab result value"""
        errors = {}
        try:
            # Check if it's a numeric value
            float(value)
        except ValueError:
            errors["value"] = [_("Lab value must be numeric")]
        return errors

    def _validate_reference_range(self, range_str: str) -> Dict[str, List[str]]:
        """Validate reference range"""
        errors = {}
        if not re.match(r"^\d+(?:\.\d+)?\s*-\s*\d+(?:\.\d+)?$", range_str):
            errors["reference_range"] = [_("Invalid reference range format")]
        return errors

    def _sanitize_dict(self, data: Dict) -> Dict:
        """Sanitize all string values in a dictionary"""
        sanitized = {}
        for key, value in data.items():
            if isinstance(value, str):
                sanitized[key] = self._sanitize_string(value)
            elif isinstance(value, dict):
                sanitized[key] = self._sanitize_dict(value)
            elif isinstance(value, list):
                sanitized[key] = [
                    (
                        self._sanitize_dict(item)
                        if isinstance(item, dict)
                        else (
                            self._sanitize_string(item)
                            if isinstance(item, str)
                            else item
                        )
                    )
                    for item in value
                ]
            else:
                sanitized[key] = value
        return sanitized

    def _sanitize_string(self, value: str) -> str:
        """Sanitize a string input"""
        # Remove HTML tags
        sanitized = strip_tags(value)
        # Escape HTML entities
        sanitized = html.escape(sanitized)
        # Remove potentially dangerous characters
        sanitized = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]", "", sanitized)
        return sanitized.strip()


class XSSCleaner:
    """
    Comprehensive XSS prevention for healthcare applications
    """

    def __init__(self):
        self.dangerous_patterns = [
            r"<script.*?>.*?</script>",
            r"javascript:",
            r"on\w+\s*=",
            r"eval\(",
            r"expression\(",
            r"url\(",
            r"import\s*",
            r"@import",
            r"<\?php",
            r"<\s*\/?\s*script\s*>",
            r"<\s*\/?\s*iframe\s*>",
            r"<\s*\/?\s*object\s*>",
            r"<\s*\/?\s*embed\s*>",
            r"<\s*\/?\s*applet\s*>",
            r"<\s*\/?\s*meta\s*>",
            r"<\s*\/?\s*link\s*>",
        ]

    def clean_input(self, value: Any) -> Any:
        """Clean input data to prevent XSS"""
        if isinstance(value, str):
            return self._clean_string(value)
        elif isinstance(value, dict):
            return {k: self.clean_input(v) for k, v in value.items()}
        elif isinstance(value, list):
            return [self.clean_input(item) for item in value]
        else:
            return value

    def _clean_string(self, value: str) -> str:
        """Clean a string to prevent XSS"""
        # Remove null bytes
        value = value.replace("\x00", "")

        # Apply HTML escaping
        value = html.escape(value)

        # Remove dangerous patterns
        for pattern in self.dangerous_patterns:
            value = re.sub(pattern, "", value, flags=re.IGNORECASE | re.DOTALL)

        # Sanitize Unicode control characters
        value = "".join(char for char in value if ord(char) >= 32 or char in "\n\r\t")

        return value

    def validate_html_content(self, content: str) -> bool:
        """
        Validate HTML content for safe rendering
        Returns True if content is safe
        """
        # Check for dangerous patterns
        for pattern in self.dangerous_patterns:
            if re.search(pattern, content, flags=re.IGNORECASE | re.DOTALL):
                return False

        # Check for event handlers
        event_handlers = [
            "onload",
            "onerror",
            "onclick",
            "onmouseover",
            "onfocus",
            "onblur",
            "onchange",
            "onsubmit",
            "onreset",
            "onselect",
            "onunload",
            "ondblclick",
            "onkeydown",
            "onkeypress",
            "onkeyup",
            "onmousedown",
            "onmouseup",
            "onmousemove",
            "onmouseout",
            "onmouseenter",
            "onmouseleave",
        ]
        content_lower = content.lower()
        for handler in event_handlers:
            if handler in content_lower:
                return False

        return True

    def sanitize_json(self, json_str: str) -> str:
        """Sanitize JSON string to prevent JSON injection"""
        try:
            # Parse and re-serialize to ensure valid JSON
            data = json.loads(json_str)
            sanitized_data = self.clean_input(data)
            return json.dumps(sanitized_data)
        except json.JSONDecodeError:
            # If invalid JSON, return empty string
            return ""


class SQLInjectionPrevention:
    """
    Prevent SQL injection attacks
    """

    def __init__(self):
        self.sql_patterns = [
            r"(union\s+select)",
            r"(insert\s+into)",
            r"(update\s+.*\s+set)",
            r"(delete\s+from)",
            r"(drop\s+(table|database))",
            r"(alter\s+table)",
            r"(create\s+(table|database|view|procedure|function))",
            r"(exec\s*\()",
            r"(execute\s*\()",
            r"(cast\s*\()",
            r"(convert\s*\()",
            r"(--)",
            r"(/\*.*\*/)",
            r"(;)",
            r"(\|\|)",
            r"(xor)",
            r"(or\s+1\s*=\s*1)",
            r"(and\s+1\s*=\s*1)",
        ]

    def detect_sql_injection(self, input_str: str) -> bool:
        """Detect potential SQL injection attempts"""
        if not isinstance(input_str, str):
            return False

        input_lower = input_str.lower()
        for pattern in self.sql_patterns:
            if re.search(pattern, input_lower, flags=re.IGNORECASE):
                return True
        return False

    def sanitize_query_param(self, param: str) -> str:
        """Sanitize query parameters"""
        if not isinstance(param, str):
            return str(param)

        # Escape single quotes
        param = param.replace("'", "''")
        # Remove semicolons
        param = param.replace(";", "")
        # Remove comment markers
        param = param.replace("--", "")
        param = param.replace("/*", "")
        param = param.replace("*/", "")

        return param.strip()


class CommandInjectionPrevention:
    """
    Prevent command injection attacks
    """

    DANGEROUS_CHARS = ["&", "|", ";", "$", "(", ")", "<", ">", "`", "\\", '"', "'"]

    def __init__(self):
        self.dangerous_commands = [
            "rm ",
            "del ",
            "rmdir ",
            "format ",
            "fdisk ",
            "wget ",
            "curl ",
            "nc ",
            "netcat ",
            "telnet ",
            "ssh ",
            "scp ",
            "ftp ",
            "tftp ",
            "whoami",
            "id",
            "pwd",
            "ls ",
            "cat ",
            "ps ",
            "kill ",
            "pkill ",
            "system(",
            "exec(",
            "eval(",
            "shell_exec(",
            "passthru(",
            "proc_open(",
        ]

    def detect_command_injection(self, input_str: str) -> bool:
        """Detect potential command injection attempts"""
        if not isinstance(input_str, str):
            return False

        input_lower = input_str.lower()

        # Check for dangerous characters
        for char in self.DANGEROUS_CHARS:
            if char in input_str:
                return True

        # Check for dangerous commands
        for cmd in self.dangerous_commands:
            if cmd in input_lower:
                return True

        return False

    def sanitize_filename(self, filename: str) -> str:
        """Sanitize filename to prevent directory traversal"""
        # Remove path separators
        filename = filename.replace("/", "_").replace("\\", "_")
        # Remove dangerous characters
        dangerous_chars = ["..", "|", "&", ";", "$", "(", ")", "<", ">", "`", '"', "'"]
        for char in dangerous_chars:
            filename = filename.replace(char, "_")
        return filename


# Global validators
healthcare_validator = HealthcareDataValidator()
xss_cleaner = XSSCleaner()
sql_prevention = SQLInjectionPrevention()
command_prevention = CommandInjectionPrevention()


def validate_healthcare_input(
    data: Dict, data_type: str = "patient"
) -> Tuple[bool, Dict[str, List[str]]]:
    """
    Validate healthcare input data
    Returns tuple of (is_valid, errors)
    """
    validators = {
        "patient": healthcare_validator.validate_patient_data,
        "medication": healthcare_validator.validate_medication_data,
        "lab_result": healthcare_validator.validate_lab_result,
    }

    if data_type not in validators:
        return False, {"data_type": [_("Invalid data type")]}

    errors = validators[data_type](data)
    return len(errors) == 0, errors


def sanitize_all_input(data: Any) -> Any:
    """
    Sanitize all input data comprehensively
    """
    # XSS prevention
    data = xss_cleaner.clean_input(data)

    # SQL injection detection (for logging/alerting)
    if isinstance(data, str) and sql_prevention.detect_sql_injection(data):
        from core.monitoring import security_monitor

        security_monitor.log_security_event(
            "SQL_INJECTION_ATTEMPT",
            severity="HIGH",
            details=f"Potential SQL injection detected: {data[:100]}",
        )

    # Command injection detection (for logging/alerting)
    if isinstance(data, str) and command_prevention.detect_command_injection(data):
        from core.monitoring import security_monitor

        security_monitor.log_security_event(
            "COMMAND_INJECTION_ATTEMPT",
            severity="HIGH",
            details=f"Potential command injection detected: {data[:100]}",
        )

    return data
