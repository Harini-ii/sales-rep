import hashlib
import secrets
from typing import Tuple


def hash_password(password: str, iterations: int = 600000) -> str:
    """
    Securely hashes a password using PBKDF2-HMAC-SHA256 with a unique random salt.
    Format: pbkdf2_sha256$<iterations>$<salt_hex>$<hash_hex>
    """
    salt = secrets.token_hex(16)
    key = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("utf-8"),
        iterations
    )
    return f"pbkdf2_sha256${iterations}${salt}${key.hex()}"


def verify_password(plain_password: str, stored_hash: str) -> bool:
    """
    Verifies a plaintext password against a stored hash or legacy baseline.
    Supports PBKDF2-SHA256 and gracefully handles mock plaintext fallback.
    Never exposes passwords in logs.
    """
    if not stored_hash or not plain_password:
        return False

    # 1. PBKDF2-SHA256 verification
    if stored_hash.startswith("pbkdf2_sha256$"):
        parts = stored_hash.split("$")
        if len(parts) == 4:
            try:
                iterations = int(parts[1])
                salt = parts[2]
                expected_key_hex = parts[3]
                computed_key = hashlib.pbkdf2_hmac(
                    "sha256",
                    plain_password.encode("utf-8"),
                    salt.encode("utf-8"),
                    iterations
                )
                return secrets.compare_digest(computed_key.hex(), expected_key_hex)
            except Exception:
                return False

    # 2. Argon2id check (if argon2_cffi is installed in future)
    if stored_hash.startswith("$argon2"):
        try:
            from argon2 import PasswordHasher
            ph = PasswordHasher()
            ph.verify(stored_hash, plain_password)
            return True
        except ImportError:
            # argon2-cffi not installed in current environment
            return False
        except Exception:
            return False

    # 3. Safe fallback for mock/pre-migration plaintext
    return secrets.compare_digest(stored_hash, plain_password)
