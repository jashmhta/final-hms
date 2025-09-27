"""
utils module
"""

import json
import logging
import time
import traceback
from typing import Any, Dict, List, Optional, Union

import requests
from pybreaker import CircuitBreaker
from rest_framework import status
from rest_framework.exceptions import APIException, NotFound, PermissionDenied
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework.views import exception_handler
from tenacity import retry, stop_after_attempt, wait_exponential

from django.core.exceptions import ValidationError
from django.db import models, transaction
from django.db.models import QuerySet
from django.shortcuts import get_object_or_404

logger = logging.getLogger(__name__)
api_breaker = CircuitBreaker(fail_max=5, reset_timeout=60)


class PerformanceTracker:
    def __init__(self, operation_name: str):
        self.operation_name = operation_name
        self.start_time = None
        self.end_time = None

    def __enter__(self):
        self.start_time = time.time()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.end_time = time.time()
        duration = self.end_time - self.start_time
        logger.info(f"Operation '{self.operation_name}' took {duration:.3f} seconds")

    def get_duration(self) -> float:
        if self.start_time and self.end_time:
            return self.end_time - self.start_time
        return 0.0


@api_breaker
@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
def safe_api_call(url, method="GET", **kwargs):
    return requests.request(method, url, **kwargs)


def optimize_queryset(queryset: QuerySet) -> QuerySet:
    if hasattr(queryset.model, "hospital"):
        queryset = queryset.select_related("hospital")
    if hasattr(queryset.model, "user"):
        queryset = queryset.select_related("user")
    if hasattr(queryset.model, "patient"):
        queryset = queryset.select_related("patient")
    return queryset


def custom_exception_handler(exc, context):
    """
    Custom exception handler for enhanced error responses.
    """
    logger.error(f"Exception occurred: {str(exc)}", exc_info=True)

    # Call REST framework's default exception handler first
    response = exception_handler(exc, context)

    # If response is None, it means DRF couldn't handle it
    if response is None:
        if isinstance(exc, ValidationError):
            return Response(
                {
                    "error": "Validation Error",
                    "details": (
                        exc.message_dict if hasattr(exc, "message_dict") else str(exc)
                    ),
                    "status": "error",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        elif isinstance(exc, PermissionDenied):
            return Response(
                {"error": "Permission Denied", "details": str(exc), "status": "error"},
                status=status.HTTP_403_FORBIDDEN,
            )
        elif isinstance(exc, NotFound):
            return Response(
                {"error": "Not Found", "details": str(exc), "status": "error"},
                status=status.HTTP_404_NOT_FOUND,
            )
        else:
            # Generic server error
            return Response(
                {
                    "error": "Internal Server Error",
                    "details": "An unexpected error occurred",
                    "status": "error",
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    # Enhance the response with additional information
    if response is not None:
        custom_response_data = {
            "status": "error",
            "error": response.data.get("detail", "An error occurred"),
        }

        # Add validation errors if present
        if hasattr(response.data, "items"):
            for key, value in response.data.items():
                if key != "detail":
                    custom_response_data[key] = value

        # Add trace information for debugging (only in development)
        from django.conf import settings

        if getattr(settings, "DEBUG", False):
            custom_response_data["debug"] = {
                "exception_type": type(exc).__name__,
                "exception_message": str(exc),
                "traceback": traceback.format_exc(),
            }

        response.data = custom_response_data

    return response


def get_object_or_404(model, **kwargs):
    """
    Enhanced get_object_or_404 with logging and error handling.
    """
    try:
        return model.objects.get(**kwargs)
    except model.DoesNotExist:
        logger.warning(f"{model.__name__} not found with kwargs: {kwargs}")
        raise NotFound(f"{model.__name__} not found")
    except Exception as e:
        logger.error(f"Error retrieving {model.__name__}: {str(e)}")
        raise APIException(f"Error retrieving {model.__name__}")


def paginated_response(queryset, serializer_class, request, context=None):
    """
    Create a paginated response with enhanced features.
    """
    if context is None:
        context = {}

    paginator = PageNumberPagination()
    paginator.page_size = request.query_params.get("page_size", 25)
    paginator.page_size_query_param = "page_size"
    paginator.max_page_size = 100

    page = paginator.paginate_queryset(queryset, request)
    if page is not None:
        serializer = serializer_class(page, many=True, context=context)
        return paginator.get_paginated_response(serializer.data)

    serializer = serializer_class(queryset, many=True, context=context)
    return Response(serializer.data)


def validate_required_fields(
    data: Dict[str, Any], required_fields: List[str]
) -> Dict[str, str]:
    """
    Validate required fields in request data.

    Args:
        data: Request data dictionary
        required_fields: List of required field names

    Returns:
        Dictionary of error messages for missing fields
    """
    errors = {}
    for field in required_fields:
        if field not in data or data[field] is None or data[field] == "":
            errors[field] = f"{field.replace('_', ' ').title()} is required"
    return errors


def validate_email_format(email: str) -> bool:
    """
    Validate email format.

    Args:
        email: Email string to validate

    Returns:
        True if valid, False otherwise
    """
    import re

    email_regex = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    return re.match(email_regex, email) is not None


def validate_phone_format(phone: str) -> bool:
    """
    Validate phone number format.

    Args:
        phone: Phone number string to validate

    Returns:
        True if valid, False otherwise
    """
    import re

    # Remove common separators
    clean_phone = phone.replace("-", "").replace(" ", "").replace("+", "")
    phone_regex = r"^\d{10,15}$"
    return re.match(phone_regex, clean_phone) is not None


def format_validation_errors(errors: Dict[str, Any]) -> Dict[str, Any]:
    """
    Format validation errors for API response.

    Args:
        errors: Validation errors dictionary

    Returns:
        Formatted errors dictionary
    """
    formatted_errors = {}

    for field, error in errors.items():
        if isinstance(error, list):
            formatted_errors[field] = error
        elif isinstance(error, dict):
            formatted_errors[field] = error
        else:
            formatted_errors[field] = [str(error)]

    return formatted_errors


def create_success_response(
    data: Any = None, message: str = "Success", **kwargs
) -> Response:
    """
    Create a standardized success response.

    Args:
        data: Response data
        message: Success message
        **kwargs: Additional response data

    Returns:
        Response object
    """
    response_data = {"status": "success", "message": message, "data": data}
    response_data.update(kwargs)
    return Response(response_data)


def create_error_response(
    message: str,
    status_code: int = status.HTTP_400_BAD_REQUEST,
    errors: Dict[str, Any] = None,
    **kwargs,
) -> Response:
    """
    Create a standardized error response.

    Args:
        message: Error message
        status_code: HTTP status code
        errors: Detailed error information
        **kwargs: Additional response data

    Returns:
        Response object
    """
    response_data = {
        "status": "error",
        "message": message,
    }

    if errors:
        response_data["errors"] = errors

    response_data.update(kwargs)
    return Response(response_data, status=status_code)


def get_client_ip(request) -> str:
    """
    Get client IP address from request.

    Args:
        request: Django request object

    Returns:
        Client IP address
    """
    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if x_forwarded_for:
        ip = x_forwarded_for.split(",")[0]
    else:
        ip = request.META.get("REMOTE_ADDR")
    return ip


def log_user_action(user, action: str, details: str = None, **kwargs):
    """
    Log user action for audit purposes.

    Args:
        user: User object
        action: Action performed
        details: Action details
        **kwargs: Additional log data
    """
    from .models import AuditLog

    log_data = {
        "user": user,
        "action": action,
        "details": details,
        "ip_address": kwargs.get("ip_address"),
        "user_agent": kwargs.get("user_agent"),
    }

    # Add any additional metadata
    metadata = {
        k: v for k, v in kwargs.items() if k not in ["ip_address", "user_agent"]
    }
    if metadata:
        log_data["metadata"] = json.dumps(metadata)

    AuditLog.objects.create(**log_data)


def safe_delete(model, **kwargs):
    """
    Safely delete an object with error handling.

    Args:
        model: Django model class
        **kwargs: Filter arguments

    Returns:
        True if deleted, False otherwise
    """
    try:
        obj = model.objects.get(**kwargs)
        obj.delete()
        return True
    except model.DoesNotExist:
        logger.warning(f"{model.__name__} not found for deletion with kwargs: {kwargs}")
        return False
    except Exception as e:
        logger.error(f"Error deleting {model.__name__}: {str(e)}")
        return False


def safe_update(obj, data: Dict[str, Any], exclude: List[str] = None) -> bool:
    """
    Safely update an object with data validation.

    Args:
        obj: Object to update
        data: Update data
        exclude: Fields to exclude from update

    Returns:
        True if updated, False otherwise
    """
    if exclude is None:
        exclude = []

    try:
        with transaction.atomic():
            for field, value in data.items():
                if field not in exclude and hasattr(obj, field):
                    setattr(obj, field, value)
            obj.save()
        return True
    except Exception as e:
        logger.error(f"Error updating {obj.__class__.__name__}: {str(e)}")
        return False


def get_model_field_choices(model, field_name: str) -> List[Dict[str, str]]:
    """
    Get field choices for a model as a list of dictionaries.

    Args:
        model: Django model class
        field_name: Field name to get choices for

    Returns:
        List of choice dictionaries
    """
    field = model._meta.get_field(field_name)
    if hasattr(field, "choices") and field.choices:
        return [{"value": choice[0], "label": choice[1]} for choice in field.choices]
    return []


def bulk_create_with_audit(
    model, objects_data: List[Dict[str, Any]], user, batch_size: int = 1000
) -> List[Any]:
    """
    Bulk create objects with audit logging.

    Args:
        model: Django model class
        objects_data: List of object data dictionaries
        user: User performing the action
        batch_size: Batch size for bulk creation

    Returns:
        List of created objects
    """
    try:
        objects = [model(**data) for data in objects_data]
        created_objects = model.objects.bulk_create(objects, batch_size=batch_size)

        # Log the bulk creation
        log_user_action(
            user=user,
            action="BULK_CREATE",
            details=f"Bulk created {len(created_objects)} {model.__name__} objects",
            object_count=len(created_objects),
            model_name=model.__name__,
        )

        return created_objects
    except Exception as e:
        logger.error(f"Error in bulk creating {model.__name__}: {str(e)}")
        raise


def get_queryset_with_permissions(model, user, base_queryset=None):
    """
    Get queryset filtered by user permissions.

    Args:
        model: Django model class
        user: User object
        base_queryset: Base queryset to filter (optional)

    Returns:
        Filtered queryset
    """
    if base_queryset is None:
        base_queryset = model.objects.all()

    # Superuser sees everything
    if user.is_superuser or getattr(user, "role", None) == "SUPER_ADMIN":
        return base_queryset

    # Check if user has hospital access
    hospital_id = getattr(user, "hospital_id", None)
    if hospital_id and hasattr(model, "hospital"):
        return base_queryset.filter(hospital_id=hospital_id)

    # Check if user has department access
    department_id = getattr(user, "department_id", None)
    if department_id and hasattr(model, "department"):
        return base_queryset.filter(department_id=department_id)

    # Default: return empty queryset if no specific permissions
    return base_queryset.none()
