"""
app/core/security.py
────────────────────
Authentication and authorization utilities.

Responsibilities
~~~~~~~~~~~~~~~~
* Password hashing / verification (bcrypt via passlib).
* JWT access-token creation and decoding (PyJWT).
* FastAPI dependencies for extracting the current user and enforcing
  admin-only access.
"""

from datetime import datetime, timedelta, timezone
from typing import Optional

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from passlib.context import CryptContext
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.db.session import get_db

# ── Password hashing context ────────────────────────────────────────
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# ── Bearer-token extraction scheme ──────────────────────────────────
bearer_scheme = HTTPBearer(auto_error=False)


# =====================================================================
# Password helpers
# =====================================================================

def hash_password(plain_password: str) -> str:
    """Return a bcrypt hash of the given plain-text password."""
    return pwd_context.hash(plain_password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Return ``True`` if *plain_password* matches *hashed_password*."""
    return pwd_context.verify(plain_password, hashed_password)


# =====================================================================
# JWT helpers
# =====================================================================

def create_access_token(
    data: dict,
    settings: Optional[Settings] = None,
    expires_delta: Optional[timedelta] = None,
) -> str:
    """
    Create a signed JWT containing *data* as claims.

    Parameters
    ----------
    data : dict
        Payload claims (must include ``"sub"`` with the user ID).
    settings : Settings, optional
        App settings; defaults to the cached singleton.
    expires_delta : timedelta, optional
        Custom lifetime; falls back to ``ACCESS_TOKEN_EXPIRE_MINUTES``.

    Returns
    -------
    str
        Encoded JWT string.
    """
    settings = settings or get_settings()
    to_encode = data.copy()

    expire = datetime.now(timezone.utc) + (
        expires_delta
        or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode.update({"exp": expire})

    return jwt.encode(
        to_encode,
        settings.JWT_SECRET,
        algorithm=settings.JWT_ALGORITHM,
    )


def decode_access_token(token: str, settings: Optional[Settings] = None) -> dict:
    """
    Decode and validate a JWT.

    Raises
    ------
    HTTPException (401)
        If the token is expired, malformed, or the signature is invalid.
    """
    settings = settings or get_settings()
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET,
            algorithms=[settings.JWT_ALGORITHM],
        )
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired.",
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token.",
        )


# =====================================================================
# FastAPI dependencies
# =====================================================================

async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    """
    Dependency that extracts and validates the JWT from the
    ``Authorization: Bearer <token>`` header.

    Returns the ``User`` ORM object or raises 401.
    """
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication credentials were not provided.",
        )

    payload = decode_access_token(credentials.credentials, settings)
    user_id: str = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token payload is missing 'sub' claim.",
        )

    # Import here to avoid circular imports at module level
    from app.repositories.user_repo import UserRepository

    user_repo = UserRepository(db)
    user = await user_repo.get_by_id(user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found.",
        )
    return user


async def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    """
    Same as ``get_current_user`` but returns ``None`` instead of
    raising 401 when the header is absent.  Useful for endpoints
    that work for both guests and logged-in users.
    """
    if credentials is None:
        return None

    try:
        return await get_current_user(credentials, db, settings)
    except HTTPException:
        return None


async def require_admin(
    current_user=Depends(get_current_user),
):
    """
    Dependency that enforces admin-only access.

    Raises 403 if the authenticated user does not have the ``admin`` role.
    """
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required.",
        )
    return current_user
