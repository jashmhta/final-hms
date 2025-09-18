import base64
import json
import os
import time
from typing import Optional
import requests
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding
from pybreaker import CircuitBreaker
AUDIT_URL = os.getenv(
    "AUDIT_SERVICE_URL", "https://audit_service:9015/api/audit/events"
)
SERVICE_JWT = os.getenv("SERVICE_JWT", None)
SERVICE_SHARED_KEY = os.getenv("SERVICE_SHARED_KEY", None)
AUDIT_PUBLIC_KEY_PATH = os.getenv("AUDIT_PUBLIC_KEY_PATH", None)
breaker = CircuitBreaker(fail_max=5, reset_timeout=60)
def _encrypt_payload(payload: dict) -> dict:
    if not AUDIT_PUBLIC_KEY_PATH or not os.path.exists(AUDIT_PUBLIC_KEY_PATH):
        return payload
    with open(AUDIT_PUBLIC_KEY_PATH, "rb") as f:
        pub = serialization.load_pem_public_key(f.read())
    plaintext = json.dumps(payload).encode("utf-8")
    cipher = pub.encrypt(
        plaintext,
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None,
        ),
    )
    return {
        "encrypted": True,
        "ciphertext_b64": base64.b64encode(cipher).decode("ascii"),
    }
def send_audit_event(
    service: str,
    action: str,
    resource_type: str,
    resource_id: Optional[str] = None,
    detail: Optional[str] = None,
):
    if not (SERVICE_JWT or SERVICE_SHARED_KEY):
        return
    headers = {"Content-Type": "application/json"}
    if SERVICE_JWT:
        headers["Authorization"] = f"Bearer {SERVICE_JWT}"
    if SERVICE_SHARED_KEY:
        headers["X-Service-Key"] = SERVICE_SHARED_KEY
    payload = {
        "service": service,
        "action": action,
        "resource_type": resource_type,
        "resource_id": resource_id,
        "detail": detail,
    }
    payload = _encrypt_payload(payload)
    @breaker
    def post():
        requests.post(AUDIT_URL, json=payload, headers=headers, timeout=2)
    for attempt in range(3):
        try:
            post()
            return
        except Exception:
            time.sleep(0.2 * (2**attempt))