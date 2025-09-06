from django.db import models
from cryptography.fernet import Fernet

# Generate a key (in production, store securely in environment variable)
FERNET_KEY = Fernet.generate_key()
fernet = Fernet(FERNET_KEY)

class EncryptedCharField(models.CharField):
    def get_prep_value(self, value):
        if value is None:
            return value
        return fernet.encrypt(value.encode()).decode()

    def from_db_value(self, value, expression, connection):
        if value is None:
            return value
        return fernet.decrypt(value.encode()).decode()

class EncryptedEmailField(EncryptedCharField):
    pass
