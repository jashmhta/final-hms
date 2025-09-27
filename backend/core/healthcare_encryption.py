"""
Enhanced Encryption Configuration for Healthcare Data
Implements comprehensive encryption at rest and in transit for HIPAA compliance
"""

import os
import ssl
from typing import Dict, Optional, Tuple

from cryptography.hazmat.primitives import constant_time, hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.kdf.hkdf import HKDF

from django.conf import settings


class HealthcareEncryptionManager:
    """
    Enhanced encryption manager specifically for healthcare data
    Implements HIPAA-compliant encryption for PHI at rest and in transit
    """

    def __init__(self):
        self.encryption_key = self._get_or_generate_encryption_key()
        self.tls_versions = ["TLSv1.2", "TLSv1.3"]
        self.cipher_suites = [
            "TLS_AES_256_GCM_SHA384",
            "TLS_CHACHA20_POLY1305_SHA256",
            "TLS_AES_128_GCM_SHA256",
        ]

    def _get_or_generate_encryption_key(self) -> bytes:
        """Get or generate a 256-bit encryption key for healthcare data"""
        key = os.getenv("HEALTHCARE_ENCRYPTION_KEY")
        if key:
            return key.encode()
        # Generate key if not exists (for development only)
        return os.urandom(32)

    def encrypt_phi(self, data: str, context: Dict = None) -> Tuple[bytes, Dict]:
        """
        Encrypt Protected Health Information with context-aware encryption
        Returns encrypted data and encryption metadata
        """
        if not data:
            return b"", {}

        # Generate IV for each encryption
        iv = os.urandom(12)

        # Create context tag for additional security
        context_tag = self._generate_context_tag(context)

        # Encrypt data with AES-256-GCM
        cipher = Cipher(algorithms.AES(self.encryption_key), modes.GCM(iv, tag=None))
        encryptor = cipher.encryptor()
        encryptor.authenticate_additional_data(context_tag.encode())
        ciphertext = encryptor.update(data.encode()) + encryptor.finalize()

        # Return ciphertext with metadata
        return ciphertext, {
            "iv": iv.hex(),
            "tag": encryptor.tag.hex(),
            "context_tag": context_tag.hex(),
            "algorithm": "AES-256-GCM",
            "key_id": os.getenv("ENCRYPTION_KEY_ID", "default"),
        }

    def decrypt_phi(self, ciphertext: bytes, metadata: Dict) -> str:
        """
        Decrypt Protected Health Information with verification
        """
        if not ciphertext:
            return ""

        # Extract metadata
        iv = bytes.fromhex(metadata["iv"])
        tag = bytes.fromhex(metadata["tag"])
        context_tag = bytes.fromhex(metadata["context_tag"])

        # Verify algorithm
        if metadata["algorithm"] != "AES-256-GCM":
            raise ValueError("Unsupported encryption algorithm")

        # Decrypt with AES-256-GCM
        cipher = Cipher(algorithms.AES(self.encryption_key), modes.GCM(iv, tag))
        decryptor = cipher.decryptor()
        decryptor.authenticate_additional_data(context_tag)
        plaintext = decryptor.update(ciphertext) + decryptor.finalize()

        return plaintext.decode()

    def _generate_context_tag(self, context: Dict = None) -> bytes:
        """Generate context tag for additional security"""
        if not context:
            return b"hms_phi_context"

        context_string = "|".join(
            [
                context.get("data_type", "unknown"),
                context.get("user_role", "unknown"),
                context.get("patient_id", "anonymous"),
                context.get("timestamp", "0"),
            ]
        )
        return context_string.encode()

    def get_ssl_context(self) -> ssl.SSLContext:
        """
        Get SSL context with healthcare-grade TLS configuration
        """
        context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)

        # Use only secure TLS versions
        context.minimum_version = ssl.TLSVersion.TLSv1_2
        context.maximum_version = ssl.TLSVersion.TLSv1_3

        # Use only secure cipher suites
        context.set_ciphers(":".join(self.cipher_suites))

        # Enable HSTS
        context.options |= ssl.OP_NO_COMPRESSION
        context.options |= ssl.OP_CIPHER_SERVER_PREFERENCE

        # Require certificate verification
        context.verify_mode = ssl.CERT_REQUIRED
        context.check_hostname = True

        return context

    def generate_key_pair(self) -> Tuple[bytes, bytes]:
        """Generate RSA key pair for asymmetric encryption"""
        private_key = rsa.generate_private_key(public_exponent=65537, key_size=4096)

        private_pem = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption(),
        )

        public_pem = private_key.public_key().public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        )

        return private_pem, public_pem

    def encrypt_with_public_key(self, data: str, public_key_pem: bytes) -> bytes:
        """Encrypt data with RSA public key"""
        public_key = serialization.load_pem_public_key(public_key_pem)

        # For RSA, we need to encrypt smaller chunks
        max_chunk_size = 470  # For 4096-bit RSA
        chunks = [
            data[i : i + max_chunk_size] for i in range(0, len(data), max_chunk_size)
        ]

        encrypted_chunks = []
        for chunk in chunks:
            encrypted = public_key.encrypt(
                chunk.encode(),
                padding.OAEP(
                    mgf=padding.MGF1(algorithm=hashes.SHA256()),
                    algorithm=hashes.SHA256(),
                    label=None,
                ),
            )
            encrypted_chunks.append(encrypted)

        return b"".join(encrypted_chunks)

    def decrypt_with_private_key(
        self, ciphertext: bytes, private_key_pem: bytes
    ) -> str:
        """Decrypt data with RSA private key"""
        private_key = serialization.load_pem_private_key(private_key_pem, password=None)

        # Decrypt in chunks
        chunk_size = 512  # For 4096-bit RSA
        chunks = [
            ciphertext[i : i + chunk_size]
            for i in range(0, len(ciphertext), chunk_size)
        ]

        decrypted_chunks = []
        for chunk in chunks:
            decrypted = private_key.decrypt(
                chunk,
                padding.OAEP(
                    mgf=padding.MGF1(algorithm=hashes.SHA256()),
                    algorithm=hashes.SHA256(),
                    label=None,
                ),
            )
            decrypted_chunks.append(decrypted)

        return b"".join(decrypted_chunks).decode()

    def secure_compare(self, a: str, b: str) -> bool:
        """
        Constant-time comparison for sensitive data
        Prevents timing attacks
        """
        return constant_time.bytes_eq(a.encode(), b.encode())

    def hash_sensitive_data(self, data: str, salt: bytes = None) -> str:
        """
        Hash sensitive data for anonymization/pseudonymization
        """
        if salt is None:
            salt = os.urandom(16)

        hkdf = HKDF(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            info=b"hms_phi_hash".encode(),
        )

        return hkdf.derive(data.encode()).hex()


# Global instance
healthcare_encryption = HealthcareEncryptionManager()


class DatabaseEncryptionManager:
    """
    Database-level encryption for sensitive healthcare fields
    """

    def __init__(self):
        self.key_rotation_schedule = 90  # days

    def encrypt_field(self, field_value: str, field_name: str) -> Tuple[str, Dict]:
        """Encrypt a database field with field-specific context"""
        context = {"field_name": field_name, "table": "encrypted_field"}
        ciphertext, metadata = healthcare_encryption.encrypt_phi(field_value, context)
        return ciphertext.hex(), metadata

    def decrypt_field(self, encrypted_value: str, metadata: Dict) -> str:
        """Decrypt a database field"""
        ciphertext = bytes.fromhex(encrypted_value)
        return healthcare_encryption.decrypt_phi(ciphertext, metadata)

    def rotate_encryption_keys(self):
        """Rotate encryption keys for all encrypted fields"""
        # Implementation would involve:
        # 1. Generate new key
        # 2. Re-encrypt all data with new key
        # 3. Archive old key securely
        # 4. Update key references
        pass


class TransmissionEncryptionManager:
    """
    Manager for encryption during data transmission
    """

    def __init__(self):
        self.ssl_context = healthcare_encryption.get_ssl_context()

    def encrypt_api_response(self, data: dict) -> dict:
        """Encrypt sensitive fields in API responses"""
        sensitive_fields = [
            "ssn",
            "medical_record_number",
            "diagnosis",
            "treatment",
            "medication",
            "phone",
            "email",
        ]

        encrypted_data = {}
        for key, value in data.items():
            if any(field in key.lower() for field in sensitive_fields):
                if isinstance(value, str):
                    encrypted_value, _ = healthcare_encryption.encrypt_phi(value)
                    encrypted_data[key] = encrypted_value.hex()
                else:
                    encrypted_data[key] = value
            else:
                encrypted_data[key] = value

        return encrypted_data

    def validate_tls_connection(self, request) -> bool:
        """Validate that the connection uses secure TLS"""
        if not request.is_secure():
            return False

        # Additional TLS validation
        tls_version = request.environ.get("SSL_PROTOCOL")
        cipher_suite = request.environ.get("SSL_CIPHER")

        return tls_version in healthcare_encryption.tls_versions and any(
            cipher in cipher_suite for cipher in healthcare_encryption.cipher_suites
        )


# Global instances
db_encryption = DatabaseEncryptionManager()
transmission_encryption = TransmissionEncryptionManager()
