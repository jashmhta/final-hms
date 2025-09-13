import threading
import uuid
from typing import Optional

from django.utils.deprecation import MiddlewareMixin

_request_local = threading.local()


def get_request_id() -> Optional[str]:
    return getattr(_request_local, "request_id", None)


class RequestIdMiddleware(MiddlewareMixin):
    def process_request(self, request):
        rid = request.META.get("HTTP_X_REQUEST_ID") or str(uuid.uuid4())
        _request_local.request_id = rid
        request.request_id = rid

    def process_response(self, request, response):
        rid = getattr(request, "request_id", None) or get_request_id()
        if rid:
            response["X-Request-ID"] = rid
        return response


class SecurityHeadersMiddleware(MiddlewareMixin):
    def process_response(self, request, response):
        csp = (
            "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data:; font-src 'self' data:; connect-src 'self'"
        )
        response.setdefault("Content-Security-Policy", csp)
        response.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
        response.setdefault(
            "Permissions-Policy", "geolocation=(), microphone=(), camera=()"
        )
        return response
