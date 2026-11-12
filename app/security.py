import datetime as dt
import hashlib
import hmac
import os

import jwt

from . import config

ITERATIONS = 200_000


def hash_password(password: str) -> str:
    """PBKDF2-SHA256 with a random salt. Stored as 'salt$hash' (hex)."""
    salt = os.urandom(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, ITERATIONS)
    return f"{salt.hex()}${digest.hex()}"


def verify_password(password: str, stored: str) -> bool:
    try:
        salt_hex, digest_hex = stored.split("$")
        salt = bytes.fromhex(salt_hex)
    except ValueError:
        return False
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, ITERATIONS)
    return hmac.compare_digest(digest.hex(), digest_hex)


def create_token(user_id: int) -> str:
    expires = dt.datetime.now(dt.timezone.utc) + dt.timedelta(minutes=config.TOKEN_EXPIRE_MINUTES)
    return jwt.encode({"sub": str(user_id), "exp": expires}, config.SECRET_KEY, algorithm="HS256")


def decode_token(token: str):
    """Return the user id from a valid token, otherwise None."""
    try:
        payload = jwt.decode(token, config.SECRET_KEY, algorithms=["HS256"])
        return int(payload["sub"])
    except (jwt.PyJWTError, KeyError, ValueError):
        return None
