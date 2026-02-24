import hashlib
import os
import secrets

PBKDF2_ITERATIONS = 390000


def hash_password(password: str) -> str:
    salt = os.urandom(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        PBKDF2_ITERATIONS,
    )
    return f"juk${PBKDF2_ITERATIONS}${salt.hex()}${digest.hex()}"


def generate_api_key() -> str:
    return secrets.token_urlsafe(48)