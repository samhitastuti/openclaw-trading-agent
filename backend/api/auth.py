"""
Auth API: register, login, and optional current-user lookup.
"""

from __future__ import annotations

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from backend.api.schemas import (
    AuthLoginRequest,
    AuthRegisterRequest,
    AuthTokenResponse,
    AuthUserOut,
)
from backend.auth.service import (
    authenticate_user,
    create_access_token,
    decode_token,
    register_user,
)

logger = logging.getLogger(__name__)

router = APIRouter()
bearer_scheme = HTTPBearer(auto_error=False)


def _auth_user_response(user_id: int, email: str, full_name: str) -> AuthTokenResponse:
    token = create_access_token(user_id, email)
    return AuthTokenResponse(
        access_token=token,
        user=AuthUserOut(id=user_id, email=email, full_name=full_name),
    )


@router.post("/register", response_model=AuthTokenResponse)
async def auth_register(body: AuthRegisterRequest) -> AuthTokenResponse:
    try:
        uid, email, full_name = register_user(
            body.full_name, body.email, body.password
        )
    except ValueError as e:
        if "already exists" in str(e):
            raise HTTPException(status_code=409, detail=str(e)) from e
        raise HTTPException(status_code=400, detail=str(e)) from e
    logger.info("Registered user id=%s email=%s", uid, email)
    return _auth_user_response(uid, email, full_name)


@router.post("/login", response_model=AuthTokenResponse)
async def auth_login(body: AuthLoginRequest) -> AuthTokenResponse:
    row = authenticate_user(body.email, body.password)
    if row is None:
        raise HTTPException(status_code=401, detail="Invalid email or password.")
    uid, email, full_name = row
    logger.info("Login user id=%s email=%s", uid, email)
    return _auth_user_response(uid, email, full_name)


async def optional_current_user(
    creds: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
) -> Optional[AuthUserOut]:
    if creds is None or creds.scheme.lower() != "bearer":
        return None
    try:
        payload = decode_token(creds.credentials)
        uid = int(payload["sub"])
        email = str(payload["email"])
    except Exception:
        return None
    return AuthUserOut(id=uid, email=email, full_name="")


@router.get("/me", response_model=AuthUserOut)
async def auth_me(user: Optional[AuthUserOut] = Depends(optional_current_user)) -> AuthUserOut:
    if user is None:
        raise HTTPException(status_code=401, detail="Not authenticated.")
    # Fill full_name from DB when token lacks it
    from backend.database.db import get_connection

    with get_connection() as conn:
        row = conn.execute(
            "SELECT full_name FROM users WHERE id = ?", (user.id,)
        ).fetchone()
    full_name = str(row["full_name"]) if row else ""
    return AuthUserOut(id=user.id, email=user.email, full_name=full_name)
