import pytest
from cryptography.fernet import Fernet

from ....app.fields import EncryptedCharField, EncryptedTextField


@pytest.mark.django_db
class TestEncryptionFields:
    def test_encrypted_char_field(self):
        # Test encryption and decryption
        field = EncryptedCharField(max_length=100)
        value = "Test Encrypted Value"

        # Encrypt
        encrypted = field.get_prep_value(value)
        assert encrypted is not None
        assert encrypted != value  # Should be encrypted

        # Decrypt
        decrypted = field.from_db_value(encrypted, None, None)
        assert decrypted == value

    def test_encrypted_text_field(self):
        field = EncryptedTextField()
        long_value = "This is a very long encrypted text field value that should be properly encrypted and decrypted for HIPAA compliance testing purposes."

        encrypted = field.get_prep_value(long_value)
        assert encrypted is not None

        decrypted = field.from_db_value(encrypted, None, None)
        assert decrypted == long_value

    def test_encryption_error_handling(self):
        field = EncryptedCharField()
        invalid_token = b"gAAAAAB..."  # Invalid encrypted token

        result = field.from_db_value(invalid_token, None, None)
        assert result == "[ENCRYPTED_DATA_CORRUPTED]"
