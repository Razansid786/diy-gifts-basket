
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.user import (
    ForgotPasswordRequest,
    ResetPasswordRequest,
    TokenResponse,
    UserCreate,
    UserLogin,
)
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post(
    "/register",
    response_model=TokenResponse,
    status_code=201,
    summary="Register a new account (FR1)",
)
async def register(data: UserCreate, db: AsyncSession = Depends(get_db)):

    service = AuthService(db)
    return await service.register(data)

@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Login with email and password (FR2)",
)
async def login(data: UserLogin, db: AsyncSession = Depends(get_db)):

    service = AuthService(db)
    return await service.login(data)

@router.post(
    "/guest",
    summary="Generate a guest session ID (FR5)",
)
async def guest_session():

    session_id = AuthService.generate_guest_session()
    return {"session_id": session_id}

@router.post(
    "/forgot-password",
    summary="Request a password reset link",
)
async def forgot_password(data: ForgotPasswordRequest, db: AsyncSession = Depends(get_db)):

    service = AuthService(db)
    return await service.forgot_password(data)

@router.post(
    "/reset-password",
    summary="Reset password using a token",
)
async def reset_password(data: ResetPasswordRequest, db: AsyncSession = Depends(get_db)):

    service = AuthService(db)
    return await service.reset_password(data)