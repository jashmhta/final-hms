import os
from typing import Any

from cryptography.fernet import Fernet, InvalidToken
from django.db import models
from django.utils.encoding import force_str


def _get_fernet():
    key = os.environ.get("FERNET_KEY")
    if not key:
        # Dev fallback key embedded to avoid crashes; override via env FERNET_KEY
        key = "aQl1cJsC2OJ3n4PY9KruMCOqJpPfeNlL8A9aqXyipN4="
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
            # value likely already plaintext (first run / legacy); return as-is
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


# Optional: fallback aliases some apps expect
EncryptedField = EncryptedCharField
