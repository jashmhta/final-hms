"""
Enterprise Data Loss Prevention (DLP) System
Prevents unauthorized exfiltration of sensitive data including:
- PHI (Protected Health Information)
- PII (Personally Identifiable Information)
- Financial data
- Intellectual property
"""

import base64
import hashlib
import json
import logging
import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set, Tuple, Union
from urllib.parse import urlparse

from django.conf import settings
from django.core.cache import cache
from django.db import models
from django.http import HttpRequest, HttpResponse
from django.utils import timezone

from core.encryption import decrypt_data, encrypt_data
from core.security_compliance import log_security_event

logger = logging.getLogger(__name__)


class DataClassifier:
    """Classifies data based on sensitivity and type"""

    SENSITIVITY_LEVELS = {
        "PUBLIC": 0,
        "INTERNAL": 1,
        "CONFIDENTIAL": 2,
        "RESTRICTED": 3,
        "CRITICAL": 4,
    }

    DATA_TYPES = {
        "PHI": "Protected Health Information",
        "PII": "Personally Identifiable Information",
        "FINANCIAL": "Financial Information",
        "MEDICAL_RECORD": "Medical Record",
        "PAYMENT_CARD": "Payment Card Data",
        "INTELLECTUAL_PROPERTY": "Intellectual Property",
        "CREDENTIALS": "Credentials and Secrets",
    }

    def __init__(self):
        self.patterns = self._load_detection_patterns()
        self.keywords = self._load_keywords()

    def _load_detection_patterns(self) -> Dict[str, List[re.Pattern]]:
        """Load regex patterns for data detection"""
        return {
            "SSN": [
                re.compile(r"\b\d{3}-\d{2}-\d{4}\b"),
                re.compile(r"\b\d{3}\s\d{2}\s\d{4}\b"),
                re.compile(r"\b\d{9}\b"),
            ],
            "CREDIT_CARD": [
                re.compile(
                    r"\b(?:4[0-9]{12}(?:[0-9]{3})?|5[1-5][0-9]{14}|3[47][0-9]{13}|3[0-9]{13}|6(?:011|5[0-9]{2})[0-9]{12})\b"
                ),
                re.compile(r"\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b"),
            ],
            "EMAIL": [
                re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"),
            ],
            "PHONE": [
                re.compile(r"\b\d{3}[-.\s]?\d{3}[-.\s]?\d{4}\b"),
                re.compile(r"\b\(\d{3}\)\s*\d{3}[-.\s]?\d{4}\b"),
                re.compile(r"\b\d{1,3}[-.\s]?\d{3}[-.\s]?\d{3}[-.\s]?\d{4}\b"),
            ],
            "MEDICAL_RECORD": [
                re.compile(r"\bMRN\s*[#:]?\s*\d+\b", re.IGNORECASE),
                re.compile(r"\bMedical Record Number\s*[:=]?\s*\d+\b", re.IGNORECASE),
                re.compile(r"\bPatient ID\s*[:=]?\s*\d+\b", re.IGNORECASE),
            ],
            "LICENSE": [
                re.compile(r"\b[A-Z]\d{7}\b"),  # US Driver's License format
                re.compile(r"\b\d{8}[A-Z]\b"),  # Other license formats
            ],
            "PASSPORT": [
                re.compile(r"\b[A-Z]{1,2}\d{7,9}\b"),
            ],
            "BANK_ACCOUNT": [
                re.compile(r"\b\d{8,17}\b"),  # Various bank account formats
            ],
            "IBAN": [
                re.compile(r"\b[A-Z]{2}\d{2}[A-Z0-9]{11,30}\b"),
            ],
            "IP_ADDRESS": [
                re.compile(r"\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b"),
            ],
        }

    def _load_keywords(self) -> Dict[str, List[str]]:
        """Load keywords for sensitive data detection"""
        return {
            "PHI": [
                "patient",
                "diagnosis",
                "treatment",
                "medication",
                "prescription",
                "symptoms",
                "doctor",
                "nurse",
                "hospital",
                "clinic",
                "medical",
                "health",
                "disease",
                "condition",
                "therapy",
                "surgery",
            ],
            "FINANCIAL": [
                "salary",
                "income",
                "revenue",
                "profit",
                "credit",
                "debit",
                "account",
                "bank",
                "payment",
                "invoice",
                "receipt",
            ],
            "CONFIDENTIAL": [
                "confidential",
                "secret",
                "private",
                "sensitive",
                "internal",
                "proprietary",
                "classified",
                "restricted",
            ],
        }

    def classify_data(self, data: str) -> Dict:
        """Classify data and return sensitivity level"""
        result = {
            "sensitivity": "PUBLIC",
            "data_types": [],
            "matches": [],
            "risk_score": 0,
        }

        # Check each pattern
        for data_type, patterns in self.patterns.items():
            for pattern in patterns:
                matches = pattern.findall(data)
                if matches:
                    result["data_types"].append(data_type)
                    result["matches"].extend(matches)

        # Check keywords
        for category, keywords in self.keywords.items():
            found_keywords = []
            for keyword in keywords:
                if keyword.lower() in data.lower():
                    found_keywords.append(keyword)

            if found_keywords:
                result["data_types"].append(category)
                result["matches"].extend(found_keywords)

        # Determine sensitivity level
        if "CREDIT_CARD" in result["data_types"]:
            result["sensitivity"] = "CRITICAL"
            result["risk_score"] = 100
        elif "SSN" in result["data_types"]:
            result["sensitivity"] = "CRITICAL"
            result["risk_score"] = 90
        elif "PHI" in result["data_types"]:
            result["sensitivity"] = "RESTRICTED"
            result["risk_score"] = 80
        elif "MEDICAL_RECORD" in result["data_types"]:
            result["sensitivity"] = "RESTRICTED"
            result["risk_score"] = 75
        elif "FINANCIAL" in result["data_types"]:
            result["sensitivity"] = "CONFIDENTIAL"
            result["risk_score"] = 60
        elif "CONFIDENTIAL" in result["data_types"]:
            result["sensitivity"] = "CONFIDENTIAL"
            result["risk_score"] = 50
        elif result["data_types"]:
            result["sensitivity"] = "INTERNAL"
            result["risk_score"] = 30

        return result


class DataMasker:
    """Masks sensitive data based on policies"""

    def __init__(self):
        self.masking_rules = self._load_masking_rules()

    def _load_masking_rules(self) -> Dict:
        """Load data masking rules"""
        return {
            "SSN": {
                "method": "partial_mask",
                "mask_char": "*",
                "show_chars": 4,
                "show_position": "end",
            },
            "CREDIT_CARD": {
                "method": "partial_mask",
                "mask_char": "*",
                "show_chars": 4,
                "show_position": "end",
            },
            "EMAIL": {
                "method": "email_mask",
            },
            "PHONE": {
                "method": "partial_mask",
                "mask_char": "*",
                "show_chars": 3,
                "show_position": "end",
            },
            "MEDICAL_RECORD": {
                "method": "hash_mask",
            },
        }

    def mask_data(self, data: str, data_type: str) -> str:
        """Mask sensitive data"""
        if data_type not in self.masking_rules:
            return data

        rule = self.masking_rules[data_type]

        if rule["method"] == "partial_mask":
            return self._partial_mask(data, rule)
        elif rule["method"] == "email_mask":
            return self._email_mask(data)
        elif rule["method"] == "hash_mask":
            return self._hash_mask(data)

        return data

    def _partial_mask(self, data: str, rule: Dict) -> str:
        """Partially mask data"""
        show_chars = rule.get("show_chars", 4)
        mask_char = rule.get("mask_char", "*")
        position = rule.get("show_position", "end")

        if position == "end":
            visible = data[-show_chars:]
            masked = mask_char * (len(data) - show_chars) + visible
        else:
            visible = data[:show_chars]
            masked = visible + mask_char * (len(data) - show_chars)

        return masked

    def _email_mask(self, email: str) -> str:
        """Mask email address"""
        parts = email.split("@")
        if len(parts) != 2:
            return email

        username = parts[0]
        domain = parts[1]

        # Show first 2 characters of username
        masked_username = username[:2] + "*" * (len(username) - 2)
        return f"{masked_username}@{domain}"

    def _hash_mask(self, data: str) -> str:
        """Replace with hash"""
        return f"HASH:{hashlib.sha256(data.encode()).hexdigest()[:16]}"


class DLPPolicy:
    """DLP policy engine"""

    def __init__(self):
        self.policies = self._load_policies()
        self.classifier = DataClassifier()
        self.masker = DataMasker()

    def _load_policies(self) -> List[Dict]:
        """Load DLP policies"""
        return [
            {
                "name": "Block PHI exfiltration",
                "description": "Block any attempt to exfiltrate PHI data",
                "enabled": True,
                "data_types": ["PHI", "MEDICAL_RECORD"],
                "sensitivity_threshold": "RESTRICTED",
                "action": "block",
                "notify": True,
            },
            {
                "name": "Mask PII in logs",
                "description": "Mask PII data in application logs",
                "enabled": True,
                "data_types": ["SSN", "CREDIT_CARD", "EMAIL", "PHONE"],
                "sensitivity_threshold": "CONFIDENTIAL",
                "action": "mask",
                "notify": False,
            },
            {
                "name": "Alert on financial data access",
                "description": "Alert when financial data is accessed outside business hours",
                "enabled": True,
                "data_types": ["FINANCIAL", "BANK_ACCOUNT", "IBAN"],
                "sensitivity_threshold": "CONFIDENTIAL",
                "action": "alert",
                "notify": True,
                "conditions": {
                    "time_restrictions": True,
                    "business_hours_only": True,
                },
            },
            {
                "name": "Block credential exfiltration",
                "description": "Block any attempt to exfiltrate credentials",
                "enabled": True,
                "data_types": ["CREDENTIALS"],
                "sensitivity_threshold": "CRITICAL",
                "action": "block",
                "notify": True,
            },
        ]

    def evaluate_request(self, request: HttpRequest, data: str = None) -> Dict:
        """Evaluate DLP policies for a request"""
        if not data:
            # Extract data from request
            data = self._extract_request_data(request)

        classification = self.classifier.classify_data(data)
        policy_actions = []

        for policy in self.policies:
            if not policy["enabled"]:
                continue

            # Check if policy applies
            if self._policy_applies(policy, classification, request):
                policy_actions.append(
                    {
                        "policy": policy["name"],
                        "action": policy["action"],
                        "notify": policy.get("notify", False),
                    }
                )

                # Execute policy action
                if policy["action"] == "block":
                    return {
                        "allow": False,
                        "reason": f"Blocked by DLP policy: {policy['name']}",
                        "classification": classification,
                        "policy": policy["name"],
                    }

        return {
            "allow": True,
            "classification": classification,
            "policy_actions": policy_actions,
        }

    def _policy_applies(self, policy: Dict, classification: Dict, request: HttpRequest) -> bool:
        """Check if a policy applies to the current request"""
        # Check data types
        if not any(data_type in classification["data_types"] for data_type in policy["data_types"]):
            return False

        # Check sensitivity threshold
        sensitivity_order = ["PUBLIC", "INTERNAL", "CONFIDENTIAL", "RESTRICTED", "CRITICAL"]
        policy_threshold = sensitivity_order.index(policy["sensitivity_threshold"])
        data_sensitivity = sensitivity_order.index(classification["sensitivity"])

        if data_sensitivity < policy_threshold:
            return False

        # Check additional conditions
        conditions = policy.get("conditions", {})
        if conditions.get("time_restrictions"):
            if not self._check_time_conditions(conditions, request):
                return False

        return True

    def _check_time_conditions(self, conditions: Dict, request: HttpRequest) -> bool:
        """Check time-based conditions"""
        if conditions.get("business_hours_only"):
            current_hour = timezone.now().hour
            business_hours = range(9, 18)  # 9 AM to 6 PM
            return current_hour in business_hours

        return True

    def _extract_request_data(self, request: HttpRequest) -> str:
        """Extract data from request"""
        data_parts = []

        # Add query parameters
        if request.GET:
            data_parts.append(str(request.GET))

        # Add request body
        if hasattr(request, "body") and request.body:
            try:
                body_data = request.body.decode("utf-8")
                data_parts.append(body_data)
            except:
                pass

        # Add headers (excluding sensitive ones)
        sensitive_headers = ["AUTHORIZATION", "COOKIE"]
        for key, value in request.META.items():
            if not any(sensitive in key.upper() for sensitive in sensitive_headers):
                data_parts.append(f"{key}: {value}")

        return " ".join(data_parts)

    def mask_sensitive_data(self, data: str, user_permissions: List[str] = None) -> str:
        """Mask sensitive data based on policies"""
        if not user_permissions:
            user_permissions = []

        # Check if user has permission to view sensitive data
        if "view.unmasked.data" in user_permissions:
            return data

        # Apply masking based on classification
        classification = self.classifier.classify_data(data)
        masked_data = data

        for data_type in classification["data_types"]:
            if data_type in self.masker.masking_rules:
                # Find and mask all instances
                pattern = self.classifier.patterns.get(data_type, [])
                for p in pattern:
                    matches = p.findall(data)
                    for match in matches:
                        masked = self.masker.mask_data(match, data_type)
                        masked_data = masked_data.replace(match, masked)

        return masked_data


class DLPScanner:
    """Scans files and data stores for sensitive information"""

    def __init__(self):
        self.classifier = DataClassifier()
        self.policy = DLPPolicy()

    def scan_file(self, file_path: str, file_type: str = None) -> Dict:
        """Scan file for sensitive data"""
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()

            return self.scan_content(content, file_type)
        except Exception as e:
            logger.error(f"Error scanning file {file_path}: {str(e)}")
            return {"error": str(e)}

    def scan_content(self, content: str, content_type: str = None) -> Dict:
        """Scan content for sensitive data"""
        classification = self.classifier.classify_data(content)

        result = {
            "scanned_at": datetime.now().isoformat(),
            "content_type": content_type,
            "classification": classification,
            "findings": [],
        }

        # Generate findings for each match
        for data_type in classification["data_types"]:
            result["findings"].append(
                {
                    "type": data_type,
                    "count": len([m for m in classification["matches"] if data_type in m]),
                    "sensitivity": classification["sensitivity"],
                    "risk_score": classification["risk_score"],
                }
            )

        return result

    def scan_database(self, model: models.Model, field_name: str) -> Dict:
        """Scan database field for sensitive data"""
        findings = []
        total_records = 0
        sensitive_records = 0

        try:
            queryset = model.objects.all()
            total_records = queryset.count()

            for obj in queryset:
                field_value = getattr(obj, field_name)
                if field_value:
                    classification = self.classifier.classify_data(str(field_value))

                    if classification["sensitivity"] != "PUBLIC":
                        sensitive_records += 1
                        findings.append(
                            {
                                "record_id": obj.pk,
                                "field_value": str(field_value)[:100],  # Truncate for logging
                                "classification": classification,
                            }
                        )

        except Exception as e:
            logger.error(f"Error scanning database: {str(e)}")

        return {
            "model": model.__name__,
            "field": field_name,
            "total_records": total_records,
            "sensitive_records": sensitive_records,
            "findings": findings,
            "scanned_at": datetime.now().isoformat(),
        }


class DLPLogger:
    """Logs DLP events and violations"""

    def __init__(self):
        self.violations_log = []
        self.cache_prefix = "dlp_violations:"

    def log_violation(self, event_type: str, details: Dict, severity: str = "MEDIUM"):
        """Log DLP violation"""
        violation = {
            "timestamp": datetime.now().isoformat(),
            "event_type": event_type,
            "details": details,
            "severity": severity,
        }

        # Store in memory for immediate access
        self.violations_log.append(violation)

        # Keep only last 1000 violations
        if len(self.violations_log) > 1000:
            self.violations_log = self.violations_log[-1000:]

        # Store in cache for persistence
        cache_key = f"{self.cache_prefix}{event_type}"
        violations = cache.get(cache_key, [])
        violations.append(violation)
        cache.set(cache_key, violations, 86400)  # 24 hours

        # Log to security event system
        log_security_event(
            event_type=f"DLP_{event_type.upper()}",
            description=details.get("description", ""),
            severity=severity,
            user_id=details.get("user_id"),
            ip_address=details.get("ip_address"),
        )

    def get_violations(self, event_type: str = None, time_range: int = 3600) -> List[Dict]:
        """Get DLP violations"""
        violations = []

        if event_type:
            cache_key = f"{self.cache_prefix}{event_type}"
            violations = cache.get(cache_key, [])
        else:
            # Get all violations
            for key in cache.keys(f"{self.cache_prefix}*"):
                violations.extend(cache.get(key, []))

        # Filter by time range
        cutoff_time = datetime.now() - timedelta(seconds=time_range)
        violations = [v for v in violations if datetime.fromisoformat(v["timestamp"]) > cutoff_time]

        return violations

    def get_violation_stats(self) -> Dict:
        """Get violation statistics"""
        stats = {
            "total_violations": 0,
            "by_type": {},
            "by_severity": {},
            "recent_trend": [],
        }

        # Get all violations
        all_violations = self.get_violations(time_range=86400)  # Last 24 hours

        stats["total_violations"] = len(all_violations)

        # Group by type and severity
        for violation in all_violations:
            event_type = violation["event_type"]
            severity = violation["severity"]

            stats["by_type"][event_type] = stats["by_type"].get(event_type, 0) + 1
            stats["by_severity"][severity] = stats["by_severity"].get(severity, 0) + 1

        # Calculate hourly trend
        for hour in range(24):
            hour_start = datetime.now() - timedelta(hours=hour + 1)
            hour_end = datetime.now() - timedelta(hours=hour)

            hour_violations = [
                v for v in all_violations if hour_start <= datetime.fromisoformat(v["timestamp"]) < hour_end
            ]

            stats["recent_trend"].append(
                {
                    "hour": hour_start.strftime("%H:00"),
                    "count": len(hour_violations),
                }
            )

        return stats


class DLPMiddleware:
    """DLP middleware for Django"""

    def __init__(self, get_response):
        self.get_response = get_response
        self.policy = DLPPolicy()
        self.logger = DLPLogger()

    def __call__(self, request: HttpRequest):
        """Process request through DLP middleware"""

        # Skip DLP for certain paths
        if self._should_skip_dlp(request):
            return self.get_response(request)

        # Check request data
        if request.method in ["POST", "PUT", "PATCH"]:
            request_data = self._extract_request_data(request)
            dlp_result = self.policy.evaluate_request(request, request_data)

            if not dlp_result["allow"]:
                # Log violation
                self.logger.log_violation(
                    event_type="REQUEST_BLOCKED",
                    details={
                        "description": dlp_result["reason"],
                        "user_id": getattr(request.user, "id", None) if hasattr(request, "user") else None,
                        "ip_address": self._get_client_ip(request),
                        "path": request.path,
                        "classification": dlp_result["classification"],
                    },
                    severity="HIGH",
                )

                return HttpResponse(
                    json.dumps({"error": "Request blocked by DLP policy"}), content_type="application/json", status=403
                )

        # Process request
        response = self.get_response(request)

        # Check response data
        if hasattr(response, "data") and isinstance(response.data, dict):
            # Mask sensitive data in response
            user_permissions = getattr(request.user, "permissions", []) if hasattr(request, "user") else []
            masked_data = self.policy.mask_sensitive_data(json.dumps(response.data), user_permissions)
            response.data = json.loads(masked_data)

        return response

    def _should_skip_dlp(self, request: HttpRequest) -> bool:
        """Determine if DLP should be skipped for this request"""
        skip_paths = [
            "/health/",
            "/metrics/",
            "/static/",
            "/media/",
            "/admin/",
        ]

        return any(request.path.startswith(path) for path in skip_paths)

    def _extract_request_data(self, request: HttpRequest) -> str:
        """Extract data from request"""
        return self.policy._extract_request_data(request)

    def _get_client_ip(self, request: HttpRequest) -> str:
        """Get client IP address"""
        x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
        if x_forwarded_for:
            return x_forwarded_for.split(",")[0]
        return request.META.get("REMOTE_ADDR", "")


# DLP Management Commands and Utilities
def run_dlp_scan(model: models.Model, fields: List[str]) -> Dict:
    """Run DLP scan on database model"""
    scanner = DLPScanner()
    results = {}

    for field in fields:
        results[field] = scanner.scan_database(model, field)

    return results


def mask_sensitive_fields(obj: models.Model, fields: List[str], user_permissions: List[str] = None) -> Dict:
    """Mask sensitive fields in model instance"""
    policy = DLPPolicy()
    masked_data = {}

    for field in fields:
        field_value = getattr(obj, field)
        if field_value:
            masked_data[field] = policy.mask_sensitive_data(str(field_value), user_permissions)

    return masked_data
