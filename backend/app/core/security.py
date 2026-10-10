"""Security, cryptographic tokens, password hashing, and encryption utilities.

Pure Python standard library implementation with Argon2/Fernet delegates when installed.
Never raises unexpected exceptions.
"""

import base64
import hashlib
import hmac
import json
import os
import secrets
import time
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional, Tuple


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _get_secret_key() -> bytes:
    """Secret key for signing JWTs and HMAC operations."""
    key = os.getenv("AUTH_SECRET_KEY", "").strip()
    if key:
        return key.encode("utf-8")
    return b"safarsathi-dev-jwt-secret-key-change-in-prod-2026"


def _get_raw_encryption_key() -> bytes:
    """32-byte key for Fernet contact encryption."""
    env_key = os.getenv("CONTACTS_ENCRYPTION_KEY", "").strip()
    if env_key:
        try:
            decoded = base64.urlsafe_b64decode(env_key.encode("utf-8"))
            if len(decoded) == 32:
                return decoded
        except Exception:
            pass
        return hashlib.sha256(env_key.encode("utf-8")).digest()
    return hashlib.sha256(b"safarsathi-dev-default-contact-key-2026").digest()


# --- Password Hashing (Argon2id with PBKDF2-HMAC-SHA256 fallback) ---

def hash_password(password: str) -> str:
    """Hash password with Argon2id if available, or salted PBKDF2-HMAC-SHA256."""
    if not password:
        return ""
    try:
        from argon2 import PasswordHasher
        ph = PasswordHasher(time_cost=2, memory_cost=19456, parallelism=1)
        return ph.hash(password)
    except (ImportError, Exception):
        pass

    salt = secrets.token_bytes(16)
    iterations = 200_000
    derived = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iterations)
    salt_b64 = base64.b64encode(salt).decode("utf-8")
    hash_b64 = base64.b64encode(derived).decode("utf-8")
    return f"pbkdf2_sha256${iterations}${salt_b64}${hash_b64}"


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password against hash. Never raises."""
    if not plain_password or not hashed_password:
        return False
    try:
        if hashed_password.startswith("$argon2"):
            from argon2 import PasswordHasher
            from argon2.exceptions import VerifyMismatchError
            ph = PasswordHasher()
            try:
                return ph.verify(hashed_password, plain_password)
            except VerifyMismatchError:
                return False

        if hashed_password.startswith("pbkdf2_sha256$"):
            parts = hashed_password.split("$")
            if len(parts) != 4:
                return False
            iterations = int(parts[1])
            salt = base64.b64decode(parts[2].encode("utf-8"))
            expected_hash = base64.b64decode(parts[3].encode("utf-8"))
            derived = hashlib.pbkdf2_hmac("sha256", plain_password.encode("utf-8"), salt, iterations)
            return hmac.compare_digest(derived, expected_hash)
            
        return False
    except Exception:
        return False


# --- Token Signing & JWT standard (RFC 7519) ---

def _b64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode("utf-8").rstrip("=")


def _b64url_decode(data: str) -> bytes:
    padding = 4 - (len(data) % 4)
    if padding != 4:
        data += "=" * padding
    return base64.urlsafe_b64decode(data.encode("utf-8"))


def create_access_token(user_id: str, email: str, is_admin: bool = False, expires_in_minutes: int = 15) -> str:
    """Create a signed JWT access token valid for 15 minutes."""
    now_ts = int(time.time())
    exp_ts = now_ts + (expires_in_minutes * 60)
    header = {"alg": "HS256", "typ": "JWT"}
    payload = {
        "sub": str(user_id),
        "email": email,
        "is_admin": is_admin,
        "iat": now_ts,
        "exp": exp_ts,
        "type": "access",
    }
    
    header_bytes = json.dumps(header, separators=(",", ":")).encode("utf-8")
    payload_bytes = json.dumps(payload, separators=(",", ":")).encode("utf-8")
    
    encoded_header = _b64url_encode(header_bytes)
    encoded_payload = _b64url_encode(payload_bytes)
    signing_input = f"{encoded_header}.{encoded_payload}".encode("utf-8")
    
    signature = hmac.new(_get_secret_key(), signing_input, hashlib.sha256).digest()
    encoded_signature = _b64url_encode(signature)
    
    return f"{encoded_header}.{encoded_payload}.{encoded_signature}"


def verify_access_token(token: str) -> Optional[Dict[str, Any]]:
    """Decode and verify JWT access token. Returns payload dict or None if invalid/expired."""
    if not token or not isinstance(token, str):
        return None
    try:
        parts = token.strip().split(".")
        if len(parts) != 3:
            return None
        
        encoded_header, encoded_payload, encoded_signature = parts
        signing_input = f"{encoded_header}.{encoded_payload}".encode("utf-8")
        expected_sig = hmac.new(_get_secret_key(), signing_input, hashlib.sha256).digest()
        actual_sig = _b64url_decode(encoded_signature)
        
        if not hmac.compare_digest(expected_sig, actual_sig):
            return None
            
        payload = json.loads(_b64url_decode(encoded_payload).decode("utf-8"))
        if payload.get("exp", 0) < int(time.time()):
            return None  # Expired
            
        return payload
    except Exception:
        return None


def generate_random_token(length_bytes: int = 32) -> str:
    """Generate a high-entropy cryptographically secure random token string."""
    return secrets.token_urlsafe(length_bytes)


def hash_token(token: str) -> str:
    """SHA-256 hash of a token for secure database storage."""
    if not token:
        return ""
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def generate_csrf_token() -> str:
    """Generate a CSRF token."""
    return secrets.token_hex(24)


# --- Contact Encryption (Fernet / AES-HMAC envelope) ---

def encrypt_phone(plain_phone: str) -> str:
    """Encrypt a phone number string. Returns base64 ciphertext. Never raises."""
    if not plain_phone:
        return ""
    try:
        try:
            from cryptography.fernet import Fernet
            key_b64 = base64.urlsafe_b64encode(_get_raw_encryption_key())
            return Fernet(key_b64).encrypt(plain_phone.encode("utf-8")).decode("utf-8")
        except ImportError:
            pass

        key = _get_raw_encryption_key()
        nonce = secrets.token_bytes(16)
        plaintext = plain_phone.encode("utf-8")
        keystream = hashlib.sha256(key + nonce).digest()[:len(plaintext)]
        ciphertext = bytes(a ^ b for a, b in zip(plaintext, keystream))
        mac = hmac.new(key, nonce + ciphertext, hashlib.sha256).digest()
        return base64.urlsafe_b64encode(b"\x01" + nonce + mac + ciphertext).decode("utf-8")
    except Exception as exc:
        return f"enc_err:{exc}"


def decrypt_phone(encrypted_payload: str) -> str:
    """Decrypt phone number string. Never raises."""
    if not encrypted_payload:
        return ""
    try:
        try:
            from cryptography.fernet import Fernet
            key_b64 = base64.urlsafe_b64encode(_get_raw_encryption_key())
            return Fernet(key_b64).decrypt(encrypted_payload.encode("utf-8")).decode("utf-8")
        except (ImportError, Exception):
            pass

        raw = base64.urlsafe_b64decode(encrypted_payload.encode("utf-8"))
        if len(raw) < 1 + 16 + 32 or raw[0] != 1:
            return "[Invalid Encrypted Phone]"
        nonce, mac, ciphertext = raw[1:17], raw[17:49], raw[49:]
        key = _get_raw_encryption_key()
        if not hmac.compare_digest(mac, hmac.new(key, nonce + ciphertext, hashlib.sha256).digest()):
            return "[Decryption Verification Failed]"
        keystream = hashlib.sha256(key + nonce).digest()[:len(ciphertext)]
        return bytes(a ^ b for a, b in zip(ciphertext, keystream)).decode("utf-8", errors="replace")
    except Exception:
        return "[Decryption Error]"
