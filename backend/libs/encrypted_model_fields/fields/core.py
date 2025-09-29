"""
core module
"""

import os
from typing import Any

from cryptography.fernet import Fernet, InvalidToken

from django.db import models
from django.utils.encoding import force_str


def _get_fernet():
    # Use secrets manager for key retrieval
    try:
        from core.secrets import get_secret
        key = get_secret("FERNET_KEY")
    except ImportError:
        # Fallback if secrets manager not available
        key = os.environ.get("FERNET_KEY")

    if not key:
        # Try to load from .env file if not in environment
        try:
            import sys
            from pathlib import Path

            base_dir = Path(__file__).resolve().parent.parent.parent.parent
            env_file = base_dir / ".env"
            if env_file.exists():
                with open(env_file, "r") as f:
                    for line in f:
                        if line.startswith("FERNET_KEY="):
                            key = line.split("=", 1)[1].strip()
                            os.environ["FERNET_KEY"] = key
                            break
        except Exception:
            pass

    if not key:
        # Fallback for development - generate a temporary key
        import base64
        import secrets

        key = base64.urlsafe_b64encode(secrets.token_bytes(32)).decode()
        os.environ["FERNET_KEY"] = key

    if isinstance(key, str):
        key = key.encode()
    return Fernet(key)


_fernet = _get_fernet()


class _EncryptedMixin:
    def _encrypt(self, value: Any) -> str:
        if value is None or value == "":
            return value
        data = force_str(value).encode("utf-8")
        token = _fernet.encrypt(data)
        return token.decode("utf-8")

    def _decrypt(self, value: Any):
        if value is None or value == "":
            return value
        try:
            data = _fernet.decrypt(force_str(value).encode("utf-8"))
            return data.decode("utf-8")
        except (InvalidToken, ValueError, TypeError):
            try:
                return force_str(value)
            except Exception:
                return value

    def get_prep_value(self, value):
        value = super().get_prep_value(value)
        if value in ("", None):
            return value
        return self._encrypt(value)

    def from_db_value(self, value, expression, connection):
        if value in ("", None):
            return value
        return self._decrypt(value)

    def to_python(self, value):
        if value in ("", None):
            return value
        return self._decrypt(value)


class EncryptedCharField(_EncryptedMixin, models.CharField):
    pass


class EncryptedTextField(_EncryptedMixin, models.TextField):
    pass


class EncryptedEmailField(_EncryptedMixin, models.EmailField):
    pass


EncryptedField = EncryptedCharField
