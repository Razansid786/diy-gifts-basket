
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.models.personalization import Personalization
from app.repositories.basket_repo import BasketRepository
from app.schemas.personalization import PersonalizationUpdate

class PersonalizationService:

    def __init__(self, db: AsyncSession):
        self.db = db
        self.basket_repo = BasketRepository(db)

    async def get_personalization(self, basket_id: str) -> Personalization:

        basket = await self.basket_repo.get_with_personalization(basket_id)
        if not basket:
            raise NotFoundError("Basket", basket_id)
        if not basket.personalization:
            raise NotFoundError("Personalization for basket", basket_id)
        return basket.personalization

    async def upsert_personalization(
        self, basket_id: str, data: PersonalizationUpdate
    ) -> Personalization:

        basket = await self.basket_repo.get_with_personalization(basket_id)
        if not basket:
            raise NotFoundError("Basket", basket_id)

        if basket.personalization:

            pers = basket.personalization
            update_data = data.model_dump(exclude_unset=True)
            for key, value in update_data.items():
                setattr(pers, key, value)
            await self.db.flush()
            return pers
        else:

            pers = Personalization(
                basket_id=basket_id,
                **data.model_dump(exclude_unset=True),
            )
            self.db.add(pers)
            await self.db.flush()
            return pers

    async def set_gift_tag_image(self, basket_id: str, image_url: str) -> Personalization:

        basket = await self.basket_repo.get_with_personalization(basket_id)
        if not basket:
            raise NotFoundError("Basket", basket_id)

        if basket.personalization:
            basket.personalization.gift_tag_image_url = image_url
            await self.db.flush()
            return basket.personalization
        else:
            pers = Personalization(
                basket_id=basket_id,
                gift_tag_image_url=image_url,
            )
            self.db.add(pers)
            await self.db.flush()
            return pers