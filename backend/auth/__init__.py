"""Authentication helpers (password hashing, JWT)."""

from backend.auth.service import (
    authenticate_user,
    create_access_token,
    decode_token,
    hash_password,
    register_user,
)

__all__ = [
    "authenticate_user",
    "create_access_token",
    "decode_token",
    "hash_password",
    "register_user",
]
