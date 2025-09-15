import re
from typing import Any, Dict

from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator


def validate_no_injection(value):
    """Validate that input doesn't contain injection patterns"""
    if not isinstance(value, str):
        return

    # SQL injection patterns
    sql_patterns = [
        r'union\s+select',
        r'union\s+all\s+select',
        r';\s*drop\s+table',
        r';\s*delete\s+from',
        r';\s*update\s+.*\s+set',
        r';\s*insert\s+into',
        r'--',
        r'/\*',
        r'\*/',
        r'xp_',
        r'sp_',
    ]

    # XSS patterns
    xss_patterns = [
        r'<script[^>]*>',
        r'javascript:',
        r'onload\s*=',
        r'onerror\s*=',
        r'onclick\s*=',
        r'<iframe[^>]*>',
        r'<object[^>]*>',
        r'<embed[^>]*>',
    ]

    all_patterns = sql_patterns + xss_patterns

    for pattern in all_patterns:
        if re.search(pattern, value, re.IGNORECASE):
            raise ValidationError(
                'Input contains potentially dangerous content',
                code='invalid_input'
            )


def validate_password_strength(value):
    """Validate password meets security requirements"""
    if len(value) < 12:
        raise ValidationError('Password must be at least 12 characters long')

    if not re.search(r'[A-Z]', value):
        raise ValidationError('Password must contain at least one uppercase letter')

    if not re.search(r'[a-z]', value):
        raise ValidationError('Password must contain at least one lowercase letter')

    if not re.search(r'\d', value):
        raise ValidationError('Password must contain at least one digit')

    if not re.search(r'[!@#$%^&*()_+\-=\[\]{};\':"\\|,.<>\/?]', value):
        raise ValidationError('Password must contain at least one special character')


# Custom validators for different data types
alphanumeric_validator = RegexValidator(
    regex=r'^[a-zA-Z0-9\s\-_\.]+$',
    message='Only alphanumeric characters, spaces, hyphens, underscores, and dots are allowed'
)

phone_validator = RegexValidator(
    regex=r'^\+?1?[-.\s]?\(?([0-9]{3})\)?[-.\s]?([0-9]{3})[-.\s]?([0-9]{4})$',
    message='Enter a valid phone number'
)

zip_code_validator = RegexValidator(
    regex=r'^\d{5}(-\d{4})?$',
    message='Enter a valid ZIP code'
)