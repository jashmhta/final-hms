"""
Enterprise-Grade Secrets Management System
Supports multiple backends: Environment, Vault, AWS Secrets Manager, Azure Key Vault
"""

import os
import json
import base64
from typing import Dict, Any, Optional
from pathlib import Path
from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import secrets


class SecretsManager:
    """Enterprise secrets management with multiple backend support"""

    def __init__(self, backend: str = "auto", master_key: Optional[str] = None):
        self.backend = backend
        self.master_key = master_key or os.getenv("SECRETS_MASTER_KEY")
        self._cache = {}

        # Initialize backend
        if backend == "auto":
            self._detect_backend()
        else:
            self._init_backend()

    def _detect_backend(self):
        """Auto-detect the best available secrets backend"""
        # Priority: Vault > AWS > Azure > Local Encrypted
        if os.getenv("VAULT_ADDR"):
            self.backend = "vault"
        elif os.getenv("AWS_REGION"):
            self.backend = "aws"
        elif os.getenv("AZURE_TENANT_ID"):
            self.backend = "azure"
        else:
            self.backend = "local"

        self._init_backend()

    def _init_backend(self):
        """Initialize the selected backend"""
        if self.backend == "vault":
            try:
                import hvac
                self.vault_client = hvac.Client(
                    url=os.getenv("VAULT_ADDR"),
                    token=os.getenv("VAULT_TOKEN")
                )
            except ImportError:
                raise ImportError("hvac required for Vault backend")
        elif self.backend == "aws":
            try:
                import boto3
                self.aws_client = boto3.client("secretsmanager")
            except ImportError:
                raise ImportError("boto3 required for AWS backend")
        elif self.backend == "azure":
            try:
                from azure.keyvault.secrets import SecretClient
                from azure.identity import DefaultAzureCredential
                credential = DefaultAzureCredential()
                vault_url = os.getenv("AZURE_KEY_VAULT_URL")
                self.azure_client = SecretClient(vault_url=vault_url, credential=credential)
            except ImportError:
                raise ImportError("azure-identity and azure-keyvault-secrets required")
        elif self.backend == "local":
            self._init_local_backend()

    def _init_local_backend(self):
        """Initialize local encrypted secrets storage"""
        if not self.master_key:
            raise ValueError("SECRETS_MASTER_KEY required for local backend")

        # Derive encryption key from master key
        salt = b'hms_enterprise_salt_2024'
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(self.master_key.encode()))
        self.fernet = Fernet(key)

        # Create secrets directory
        self.secrets_dir = Path("secrets")
        self.secrets_dir.mkdir(exist_ok=True)
        self.secrets_file = self.secrets_dir / "encrypted_secrets.json"

    def get_secret(self, key: str, default: Any = None) -> Any:
        """Retrieve a secret value"""
        if key in self._cache:
            return self._cache[key]

        try:
            if self.backend == "vault":
                secret = self.vault_client.secrets.kv.v2.read_secret_version(
                    path=f"hms/{key}"
                )
                value = secret["data"]["data"][key]
            elif self.backend == "aws":
                response = self.aws_client.get_secret_value(SecretId=f"hms/{key}")
                value = json.loads(response["SecretString"])[key]
            elif self.backend == "azure":
                secret = self.azure_client.get_secret(f"hms-{key}")
                value = secret.value
            elif self.backend == "local":
                value = self._get_local_secret(key)
            else:
                value = os.getenv(key, default)

            self._cache[key] = value
            return value
        except Exception:
            return default

    def set_secret(self, key: str, value: Any):
        """Store a secret value"""
        try:
            if self.backend == "vault":
                self.vault_client.secrets.kv.v2.create_or_update_secret(
                    path=f"hms/{key}",
                    secret={key: value}
                )
            elif self.backend == "aws":
                self.aws_client.update_secret(
                    SecretId=f"hms/{key}",
                    SecretString=json.dumps({key: value})
                )
            elif self.backend == "azure":
                self.azure_client.set_secret(f"hms-{key}", str(value))
            elif self.backend == "local":
                self._set_local_secret(key, value)

            self._cache[key] = value
        except Exception as e:
            raise RuntimeError(f"Failed to set secret {key}: {e}")

    def _get_local_secret(self, key: str) -> Any:
        """Get secret from local encrypted storage"""
        if not self.secrets_file.exists():
            raise KeyError(f"Secret {key} not found")

        with open(self.secrets_file, "rb") as f:
            encrypted_data = f.read()

        decrypted_data = self.fernet.decrypt(encrypted_data)
        secrets_dict = json.loads(decrypted_data.decode())

        if key not in secrets_dict:
            raise KeyError(f"Secret {key} not found")

        return secrets_dict[key]

    def _set_local_secret(self, key: str, value: Any):
        """Set secret in local encrypted storage"""
        secrets_dict = {}

        if self.secrets_file.exists():
            try:
                with open(self.secrets_file, "rb") as f:
                    encrypted_data = f.read()
                decrypted_data = self.fernet.decrypt(encrypted_data)
                secrets_dict = json.loads(decrypted_data.decode())
            except (InvalidToken, json.JSONDecodeError):
                # File corrupted, start fresh
                pass

        secrets_dict[key] = value

        encrypted_data = self.fernet.encrypt(json.dumps(secrets_dict).encode())
        with open(self.secrets_file, "wb") as f:
            f.write(encrypted_data)

    def rotate_master_key(self, new_master_key: str):
        """Rotate the master encryption key"""
        if self.backend != "local":
            raise NotImplementedError("Key rotation only supported for local backend")

        # Decrypt all secrets with old key
        old_secrets = {}
        if self.secrets_file.exists():
            try:
                with open(self.secrets_file, "rb") as f:
                    encrypted_data = f.read()
                decrypted_data = self.fernet.decrypt(encrypted_data)
                old_secrets = json.loads(decrypted_data.decode())
            except (InvalidToken, json.JSONDecodeError):
                pass

        # Update master key and re-initialize
        self.master_key = new_master_key
        self._init_local_backend()

        # Re-encrypt with new key
        for key, value in old_secrets.items():
            self._set_local_secret(key, value)

    @staticmethod
    def generate_master_key() -> str:
        """Generate a secure master key"""
        return secrets.token_urlsafe(32)


# Global secrets manager instance
_secrets_manager = None

def get_secrets_manager() -> SecretsManager:
    """Get the global secrets manager instance"""
    global _secrets_manager
    if _secrets_manager is None:
        _secrets_manager = SecretsManager()
    return _secrets_manager

def get_secret(key: str, default: Any = None) -> Any:
    """Convenience function to get a secret"""
    return get_secrets_manager().get_secret(key, default)

def set_secret(key: str, value: Any):
    """Convenience function to set a secret"""
    get_secrets_manager().set_secret(key, value)