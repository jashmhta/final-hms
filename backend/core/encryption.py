import base64
import hashlib
import os
from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from django.conf import settings
class DataEncryption:
    def __init__(self):
        key = getattr(settings, "FIELD_ENCRYPTION_KEY", None)
        if not key:
            key = base64.urlsafe_b64encode(
                hashlib.sha256(settings.SECRET_KEY.encode()).digest()
            )
        self.fernet = Fernet(key)
    def encrypt(self, data: str) -> str:
        if not data:
            return data
        try:
            encrypted = self.fernet.encrypt(data.encode())
            return base64.urlsafe_b64encode(encrypted).decode()
        except Exception as e:
            raise ValueError(f"Encryption failed: {e}")
    def decrypt(self, encrypted_data: str) -> str:
        if not encrypted_data:
            return encrypted_data
        try:
            encrypted_bytes = base64.urlsafe_b64decode(encrypted_data.encode())
            decrypted = self.fernet.decrypt(encrypted_bytes)
            return decrypted.decode()
        except (InvalidToken, ValueError, UnicodeDecodeError) as e:
            raise ValueError(f"Decryption failed: {e}")
    def encrypt_dict(self, data: dict) -> dict:
        encrypted_data = {}
        for key, value in data.items():
            if isinstance(value, str):
                encrypted_data[key] = self.encrypt(value)
            else:
                encrypted_data[key] = value
        return encrypted_data
    def decrypt_dict(self, encrypted_data: dict) -> dict:
        decrypted_data = {}
        for key, value in encrypted_data.items():
            if isinstance(value, str):
                try:
                    decrypted_data[key] = self.decrypt(value)
                except ValueError:
                    decrypted_data[key] = value
            else:
                decrypted_data[key] = value
        return decrypted_data
class KeyManagement:
    @staticmethod
    def generate_key() -> str:
        return base64.urlsafe_b64encode(os.urandom(32)).decode()
    @staticmethod
    def rotate_key(old_key: str, new_key: str, encrypted_data: str) -> str:
        old_fernet = Fernet(old_key.encode())
        try:
            decrypted = old_fernet.decrypt(
                base64.urlsafe_b64decode(encrypted_data.encode())
            )
        except InvalidToken:
            raise ValueError("Failed to decrypt with old key")
        new_fernet = Fernet(new_key.encode())
        encrypted = new_fernet.encrypt(decrypted)
        return base64.urlsafe_b64encode(encrypted).decode()
    @staticmethod
    def derive_key(password: str, salt: bytes = None) -> str:
        if salt is None:
            salt = os.urandom(16)
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
        return key.decode()
encryption = DataEncryption()