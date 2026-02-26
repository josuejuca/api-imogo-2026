from datetime import datetime, timedelta
import hashlib
import os
import secrets

import jwt
from jwt import PyJWTError

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


def verify_password(password: str, stored_hash: str) -> bool:
    try:
        prefix, iterations, salt_hex, digest_hex = stored_hash.split("$", 3)
    except ValueError:
        return False

    if prefix != "juk":
        return False

    try:
        iteration_count = int(iterations)
        salt = bytes.fromhex(salt_hex)
    except ValueError:
        return False

    digest = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        iteration_count,
    ).hex()
    return secrets.compare_digest(digest, digest_hex)


def generate_api_key() -> str:
    return secrets.token_urlsafe(48)


def create_jwt(payload: dict, secret: str, expires_days: int) -> str:
    expiry = datetime.utcnow() + timedelta(days=expires_days)
    token_payload = {**payload, "exp": expiry}
    return jwt.encode(token_payload, secret, algorithm="HS256")


def decode_jwt(token: str, secret: str) -> dict:
    try:
        return jwt.decode(token, secret, algorithms=["HS256"])
    except PyJWTError as exc:
        raise ValueError("invalid token") from exc