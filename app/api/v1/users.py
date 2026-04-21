"""
app/api/v1/users.py
───────────────────
User profile endpoints.

Routes:
    GET  /users/me — Get the current user's profile.
    PUT  /users/me — Update the current user's profile.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_current_user
from app.db.session import get_db
from app.schemas.user import UserResponse, UserUpdate
from app.services.user_service import UserService

router = APIRouter(prefix="/users", tags=["Users"])


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get current user profile",
)
async def get_me(current_user=Depends(get_current_user)):
    """Return the authenticated user's profile information."""
    return current_user


@router.put(
    "/me",
    response_model=UserResponse,
    summary="Update current user profile",
)
async def update_me(
    data: UserUpdate,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update the authenticated user's display name or email."""
    service = UserService(db)
    return await service.update_profile(current_user.id, data)
