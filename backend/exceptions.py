class APIException(Exception):
    """Base API exception"""

    pass


class ValidationError(APIException):
    """Validation error"""

    pass


class AuthenticationError(APIException):
    """Authentication error"""

    pass


class AuthorizationError(APIException):
    """Authorization error"""

    pass
