from __future__ import annotations

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError

from app.core.exceptions import ForbiddenError, UnauthorizedError
from app.core.security import decode_access_token

_bearer = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
) -> dict:
    """Decode JWT and return the payload. Raises 401 if token is missing or invalid."""
    if not credentials:
        raise UnauthorizedError("Authentication token required.")
    try:
        payload = decode_access_token(credentials.credentials)
    except JWTError:
        raise UnauthorizedError("Invalid or expired token.")
    return payload


async def get_current_user_optional(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
) -> dict | None:
    """Like get_current_user but returns None instead of raising for public endpoints."""
    if not credentials:
        return None
    try:
        return decode_access_token(credentials.credentials)
    except JWTError:
        return None


async def require_pro(user: dict = Depends(get_current_user)) -> dict:
    """Require at least 'pro' role."""
    if user.get("role") not in ("pro", "admin"):
        raise ForbiddenError("A Pro subscription is required for this resource.")
    return user


async def require_admin(user: dict = Depends(get_current_user)) -> dict:
    """Require 'admin' role."""
    if user.get("role") != "admin":
        raise ForbiddenError("Admin access required.")
    return user
