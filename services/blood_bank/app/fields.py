import os
from cryptography.fernet import Fernet, InvalidToken
from django.db import models
key_file = "/root/blood_bank_encryption_key.key"
with open(key_file, "rb") as f:
    key = f.read()
cipher_suite = Fernet(key)
class EncryptedFieldMixin:
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.cipher_suite = cipher_suite
    def get_prep_value(self, value):
        if value is None:
            return None
        try:
            if isinstance(value, str):
                encrypted_value = self.cipher_suite.encrypt(value.encode("utf-8"))
            else:
                encrypted_value = self.cipher_suite.encrypt(str(value).encode("utf-8"))
            return encrypted_value
        except Exception as e:
            raise ValueError(f"Encryption failed: {str(e)}")
    def from_db_value(self, value, expression, connection):
        if value is None:
            return None
        try:
            if isinstance(value, str):
                decrypted_bytes = self.cipher_suite.decrypt(value.encode("utf-8"))
            else:
                decrypted_bytes = self.cipher_suite.decrypt(value)
            return decrypted_bytes.decode("utf-8")
        except InvalidToken:
            return "[ENCRYPTED_DATA_CORRUPTED]"
        except Exception as e:
            raise ValueError(f"Decryption failed: {str(e)}")
class EncryptedCharField(EncryptedFieldMixin, models.CharField):
    pass
class EncryptedTextField(EncryptedFieldMixin, models.TextField):
    pass