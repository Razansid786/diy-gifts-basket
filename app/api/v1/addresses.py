"""
app/api/v1/addresses.py
───────────────────────
Shipping address CRUD endpoints (FR4).

Routes:
    GET    /addresses      — List all addresses for the current user.
    POST   /addresses      — Add a new address.
    PUT    /addresses/{id} — Update an existing address.
    DELETE /addresses/{id} — Delete an address.
"""

from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_current_user
from app.db.session import get_db
from app.schemas.address import AddressCreate, AddressResponse, AddressUpdate
from app.services.address_service import AddressService

router = APIRouter(prefix="/addresses", tags=["Addresses"])


@router.get(
    "/",
    response_model=List[AddressResponse],
    summary="List saved shipping addresses (FR4)",
)
async def list_addresses(
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Return all shipping addresses for the authenticated user."""
    service = AddressService(db)
    return await service.list_addresses(current_user.id)


@router.post(
    "/",
    response_model=AddressResponse,
    status_code=201,
    summary="Add a new shipping address (FR4)",
)
async def create_address(
    data: AddressCreate,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Add a new shipping address to the user's account."""
    service = AddressService(db)
    return await service.create_address(current_user.id, data)


@router.put(
    "/{address_id}",
    response_model=AddressResponse,
    summary="Update a shipping address",
)
async def update_address(
    address_id: str,
    data: AddressUpdate,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update an existing shipping address (ownership verified)."""
    service = AddressService(db)
    return await service.update_address(current_user.id, address_id, data)


@router.delete(
    "/{address_id}",
    status_code=204,
    summary="Delete a shipping address",
)
async def delete_address(
    address_id: str,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete a shipping address (ownership verified)."""
    service = AddressService(db)
    await service.delete_address(current_user.id, address_id)
