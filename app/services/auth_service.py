from datetime import timedelta
import uuid
import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.exceptions import ConflictError, ValidationError
from app.core.security import (
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)
from app.repositories.user_repo import UserRepository
from app.schemas.user import (
    ForgotPasswordRequest,
    ResetPasswordRequest,
    TokenResponse,
    UserCreate,
    UserLogin,
)
from app.utils.email import send_password_reset_email, send_welcome_email

class AuthService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.user_repo = UserRepository(db)

    async def register(self, data: UserCreate) -> TokenResponse:
        existing = await self.user_repo.get_by_email(data.email)
        if existing:
            raise ConflictError("A user with this email already exists.")

        user = await self.user_repo.create({
            "email": data.email,
            "hashed_password": hash_password(data.password),
            "full_name": data.full_name,
            "role": "customer",
        })

        asyncio.create_task(send_welcome_email(user.email, user.full_name))
        token = create_access_token({"sub": user.id, "role": user.role})
        return TokenResponse(access_token=token)

    async def login(self, data: UserLogin) -> TokenResponse:
        user = await self.user_repo.get_by_email(data.email)
        if not user or not verify_password(data.password, user.hashed_password):
            raise ValidationError("Invalid email or password.")

        if not user.is_active:
            raise ValidationError("This account has been deactivated.")

        token = create_access_token({"sub": user.id, "role": user.role})
        return TokenResponse(access_token=token)

    @staticmethod
    def generate_guest_session() -> str:
        return f"guest_{uuid.uuid4().hex}"

    async def forgot_password(self, data: ForgotPasswordRequest) -> dict:
        user = await self.user_repo.get_by_email(data.email)
        if not user:
            return {"message": "If this email is registered, a reset link will be sent."}

        token = create_access_token(
            {"sub": user.id, "purpose": "password_reset"},
            expires_delta=timedelta(minutes=15)
        )
        asyncio.create_task(send_password_reset_email(user.email, token))
        return {"message": "If this email is registered, a reset link will be sent."}

    async def reset_password(self, data: ResetPasswordRequest) -> dict:
        try:
            payload = decode_access_token(data.token)
        except Exception:
            raise ValidationError("Invalid or expired reset token.")

        if payload.get("purpose") != "password_reset":
            raise ValidationError("Invalid reset token.")

        user_id = payload.get("sub")
        user = await self.user_repo.get_by_id(user_id)
        if not user:
            raise ValidationError("User not found.")

        await self.user_repo.update(user.id, {
            "hashed_password": hash_password(data.new_password)
        })
        await self.db.commit()
        return {"message": "Password changed successfully."}