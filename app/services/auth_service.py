"""
app/services/auth_service.py
────────────────────────────
Business logic for user authentication (FR1, FR2, FR5).

Handles:
* Registration — validates uniqueness, hashes password, creates user.
* Login — verifies credentials, issues JWT.
* Guest sessions — generates anonymous session identifiers.
"""

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictError, ValidationError
from app.core.security import create_access_token, hash_password, verify_password
from app.models.user import User
from app.repositories.user_repo import UserRepository
from app.schemas.user import UserCreate, UserLogin, TokenResponse


class AuthService:
    """Orchestrates registration and login flows."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.user_repo = UserRepository(db)

    async def register(self, data: UserCreate) -> TokenResponse:
        """
        Register a new user account (FR1).

        Steps:
        1. Check that the email is not already taken.
        2. Hash the password using bcrypt.
        3. Insert the user row.
        4. Return a JWT so the user is immediately logged in.

        Raises
        ------
        ConflictError
            If the email is already registered.
        """
        existing = await self.user_repo.get_by_email(data.email)
        if existing:
            raise ConflictError("A user with this email already exists.")

        user = await self.user_repo.create({
            "email": data.email,
            "hashed_password": hash_password(data.password),
            "full_name": data.full_name,
            "role": "customer",
        })

        token = create_access_token({"sub": user.id, "role": user.role})
        return TokenResponse(access_token=token)

    async def login(self, data: UserLogin) -> TokenResponse:
        """
        Authenticate with email and password (FR2).

        Returns a JWT on success.

        Raises
        ------
        ValidationError
            If the email is not found or the password is incorrect.
        """
        user = await self.user_repo.get_by_email(data.email)
        if not user or not verify_password(data.password, user.hashed_password):
            raise ValidationError("Invalid email or password.")

        if not user.is_active:
            raise ValidationError("This account has been deactivated.")

        token = create_access_token({"sub": user.id, "role": user.role})
        return TokenResponse(access_token=token)

    @staticmethod
    def generate_guest_session() -> str:
        """
        Generate a unique session ID for guest checkout (FR5).

        The frontend stores this in localStorage and sends it as a
        header or query param on subsequent requests.
        """
        return f"guest_{uuid.uuid4().hex}"
