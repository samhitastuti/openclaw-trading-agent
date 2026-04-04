"""
User registration, login verification, and JWT issuance.
"""

from __future__ import annotations

import os
import sqlite3
from datetime import datetime, timedelta, timezone
from typing import Any, Optional, Tuple

import bcrypt
import jwt
from dotenv import load_dotenv

from backend.database.db import get_connection

load_dotenv()

JWT_SECRET = os.getenv("AUTH_JWT_SECRET", "change-me-in-production-use-openssl-rand-hex-32")
JWT_ALG = "HS256"
JWT_EXPIRE_HOURS = int(os.getenv("AUTH_JWT_EXPIRE_HOURS", "168"))
BCRYPT_MAX_PASSWORD_BYTES = 72


def hash_password(plain: str) -> str:
    raw = plain.encode("utf-8")
    if len(raw) > BCRYPT_MAX_PASSWORD_BYTES:
        raise ValueError("Password too long (max 72 bytes for bcrypt).")
    hashed = bcrypt.hashpw(raw, bcrypt.gensalt(rounds=12))
    return hashed.decode("ascii")


def verify_password(plain: str, password_hash: str) -> bool:
    raw = plain.encode("utf-8")
    if len(raw) > BCRYPT_MAX_PASSWORD_BYTES:
        return False
    try:
        return bcrypt.checkpw(raw, password_hash.encode("ascii"))
    except (ValueError, TypeError):
        return False


def register_user(full_name: str, email: str, password: str) -> Tuple[int, str, str]:
    """
    Insert a new user. Returns (user_id, email, full_name).
    Raises ValueError if email already exists.
    """
    email_norm = email.strip().lower()
    full = full_name.strip()
    ph = hash_password(password)
    with get_connection() as conn:
        try:
            cur = conn.execute(
                """
                INSERT INTO users (full_name, email, password_hash)
                VALUES (?, ?, ?)
                """,
                (full, email_norm, ph),
            )
            conn.commit()
            uid = int(cur.lastrowid)
        except sqlite3.IntegrityError as e:
            raise ValueError("An account with this email already exists.") from e
    return uid, email_norm, full


def authenticate_user(email: str, password: str) -> Optional[Tuple[int, str, str]]:
    """Return (id, email, full_name) if credentials are valid, else None."""
    email_norm = email.strip().lower()
    with get_connection() as conn:
        row = conn.execute(
            "SELECT id, email, full_name, password_hash FROM users WHERE email = ?",
            (email_norm,),
        ).fetchone()
    if row is None:
        return None
    if not verify_password(password, row["password_hash"]):
        return None
    return int(row["id"]), str(row["email"]), str(row["full_name"])


def create_access_token(user_id: int, email: str) -> str:
    now = datetime.now(timezone.utc)
    exp = now + timedelta(hours=JWT_EXPIRE_HOURS)
    payload: dict[str, Any] = {
        "sub": str(user_id),
        "email": email,
        "iat": int(now.timestamp()),
        "exp": exp,
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALG)


def decode_token(token: str) -> dict[str, Any]:
    return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALG])
