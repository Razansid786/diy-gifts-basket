
from typing import List

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ForbiddenError, NotFoundError
from app.models.address import Address
from app.repositories.address_repo import AddressRepository
from app.schemas.address import AddressCreate, AddressUpdate

class AddressService:

    def __init__(self, db: AsyncSession):
        self.db = db
        self.address_repo = AddressRepository(db)

    async def list_addresses(self, user_id: str) -> List[Address]:

        return await self.address_repo.get_by_user(user_id)

    async def create_address(self, user_id: str, data: AddressCreate) -> Address:

        if data.is_default:
            await self.address_repo.clear_default(user_id)

        return await self.address_repo.create({
            "user_id": user_id,
            **data.model_dump(),
        })

    async def update_address(
        self, user_id: str, address_id: str, data: AddressUpdate
    ) -> Address:

        address = await self._get_owned_address(user_id, address_id)

        if data.is_default:
            await self.address_repo.clear_default(user_id)

        update_data = data.model_dump(exclude_unset=True)
        updated = await self.address_repo.update(address.id, update_data)
        return updated

    async def delete_address(self, user_id: str, address_id: str) -> bool:

        await self._get_owned_address(user_id, address_id)
        return await self.address_repo.delete(address_id)

    async def _get_owned_address(self, user_id: str, address_id: str) -> Address:

        address = await self.address_repo.get_by_id(address_id)
        if not address:
            raise NotFoundError("Address", address_id)
        if address.user_id != user_id:
            raise ForbiddenError("You do not own this address.")
        return address