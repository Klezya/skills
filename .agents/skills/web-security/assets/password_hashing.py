"""
Password Hashing — argon2id (preferred) and bcrypt (alternative).

argon2id is the winner of the Password Hashing Competition and the
recommended algorithm for new projects. bcrypt remains a valid choice
for existing projects already using it.

Dependencies:
    uv add argon2-cffi          # for argon2id
    uv add bcrypt               # for bcrypt (alternative)

NEVER use: MD5, SHA1, SHA256, or hashlib.pbkdf2_hmac for password hashing.
"""


# ── Argon2id (Preferred) ────────────────────────────────────────────────────

from argon2 import PasswordHasher
from argon2.exceptions import (
    HashingError,
    InvalidHashError,
    VerificationError,
    VerifyMismatchError,
)

_argon2_hasher = PasswordHasher(
    time_cost=3,        # iterations
    memory_cost=65536,  # 64 MB
    parallelism=4,      # threads
    hash_len=32,        # output length
)


def argon2_hash(password: str) -> str:
    """Hash a password with argon2id.

    Returns a string like: $argon2id$v=19$m=65536,t=3,p=4$...
    """
    return _argon2_hasher.hash(password)


def argon2_verify(password: str, hash: str) -> bool:
    """Verify a password against an argon2id hash.

    Returns True if the password matches, False otherwise.
    Handles all argon2 exceptions gracefully.
    """
    try:
        return _argon2_hasher.verify(hash, password)
    except VerifyMismatchError:
        return False
    except (InvalidHashError, HashingError, VerificationError):
        return False


def argon2_needs_rehash(hash: str) -> bool:
    """Check if a hash needs to be re-hashed with updated parameters.

    Use this when you change the PasswordHasher parameters —
    re-hash on next successful login.
    """
    return _argon2_hasher.check_needs_rehash(hash)


# ── Bcrypt (Alternative) ────────────────────────────────────────────────────

import bcrypt


def bcrypt_hash(password: str) -> str:
    """Hash a password with bcrypt.

    Default work factor: 12 (bcrypt.gensalt() default).
    Increase to 13-14 if your server hardware allows it.
    """
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def bcrypt_verify(password: str, hash: str) -> bool:
    """Verify a password against a bcrypt hash.

    Bcrypt's comparison is timing-safe by default.
    """
    return bcrypt.checkpw(password.encode("utf-8"), hash.encode("utf-8"))


# ── Unified Interface ───────────────────────────────────────────────────────


class PasswordService:
    """Unified password hashing service.

    Supports argon2id (default) and bcrypt. Use this as a single
    entry point for all password operations.

    Usage:
        pwd_service = PasswordService()  # argon2id by default
        hash = pwd_service.hash("my-password")
        ok = pwd_service.verify("my-password", hash)
    """

    def __init__(self, algorithm: str = "argon2id"):
        if algorithm == "argon2id":
            self._hash_fn = argon2_hash
            self._verify_fn = argon2_verify
        elif algorithm == "bcrypt":
            self._hash_fn = bcrypt_hash
            self._verify_fn = bcrypt_verify
        else:
            raise ValueError(f"Unsupported algorithm: {algorithm}. Use 'argon2id' or 'bcrypt'.")

    def hash(self, password: str) -> str:
        return self._hash_fn(password)

    def verify(self, password: str, hash: str) -> bool:
        return self._verify_fn(password, hash)


# ── Example Usage ───────────────────────────────────────────────────────────

if __name__ == "__main__":
    # Argon2id (recommended)
    pwd = PasswordService("argon2id")
    h = pwd.hash("super-secret-password")
    print(f"Argon2id hash: {h}")
    print(f"Verify correct: {pwd.verify('super-secret-password', h)}")
    print(f"Verify wrong:   {pwd.verify('wrong-password', h)}")

    # Bcrypt (alternative)
    pwd_bc = PasswordService("bcrypt")
    h2 = pwd_bc.hash("super-secret-password")
    print(f"\nBcrypt hash: {h2}")
    print(f"Verify correct: {pwd_bc.verify('super-secret-password', h2)}")
    print(f"Verify wrong:   {pwd_bc.verify('wrong-password', h2)}")
