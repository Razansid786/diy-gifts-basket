"""
app/api/v1/auth.py
──────────────────
Authentication endpoints (FR1, FR2, FR5).

Routes:
    POST /auth/register — Create a new account and receive a JWT.
    POST /auth/login    — Authenticate with email + password.
    POST /auth/guest    — Generate a guest session ID.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.user import UserCreate, UserLogin, TokenResponse
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post(
    "/register",
    response_model=TokenResponse,
    status_code=201,
    summary="Register a new account (FR1)",
)
async def register(data: UserCreate, db: AsyncSession = Depends(get_db)):
    """
    Create a new user account.

    The user is immediately logged in and receives a JWT token.
    """
    service = AuthService(db)
    return await service.register(data)


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Login with email and password (FR2)",
)
async def login(data: UserLogin, db: AsyncSession = Depends(get_db)):
    """
    Authenticate with email and password.

    Returns a JWT token for subsequent authenticated requests.
    """
    service = AuthService(db)
    return await service.login(data)


@router.post(
    "/guest",
    summary="Generate a guest session ID (FR5)",
)
async def guest_session():
    """
    Generate a unique session ID for guest users.

    The frontend should store this and include it in the
    ``X-Session-ID`` header for basket and cart operations.
    """
    session_id = AuthService.generate_guest_session()
    return {"session_id": session_id}
