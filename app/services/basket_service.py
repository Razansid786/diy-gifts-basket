
from typing import List, Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm.attributes import set_committed_value

from app.core.exceptions import NotFoundError, ValidationError
from app.models.basket import Basket, BasketItem, GiftBase
from app.models.personalization import Personalization
from app.repositories.basket_repo import (
    BasketRepository,
    BasketItemRepository,
    GiftBaseRepository,
)
from app.repositories.cart_repo import CartRepository, CartItemRepository
from app.repositories.product_repo import ProductRepository
from app.schemas.basket import (
    BasketCreate,
    BasketItemAdd,
    BasketItemsSync,
    QuickBuyRequest,
    CompleteAndCartRequest,
)

class BasketService:

    def __init__(self, db: AsyncSession):
        self.db = db
        self.basket_repo = BasketRepository(db)
        self.item_repo = BasketItemRepository(db)
        self.base_repo = GiftBaseRepository(db)
        self.product_repo = ProductRepository(db)

    async def create_basket(
        self,
        user_id: Optional[str],
        data: BasketCreate,
    ) -> dict:

        create_data = {
            "user_id": user_id,
            "session_id": data.session_id,
            "base_id": None,
            "status": "draft",
        }

        base = None
        if data.base_id:
            base = await self.base_repo.get_by_id(data.base_id)
            if not base:
                raise NotFoundError("GiftBase", data.base_id)
            create_data["base_id"] = base.id

        basket = await self.basket_repo.create(create_data)

        set_committed_value(basket, "base", base)
        set_committed_value(basket, "items", [])
        total = float(base.price) if base else 0.0
        return {"basket": basket, "running_total": total}

    async def set_base(self, basket_id: str, base_id: str) -> dict:

        basket = await self._get_basket(basket_id)
        base = await self.base_repo.get_by_id(base_id)
        if not base:
            raise NotFoundError("GiftBase", base_id)

        current_count = sum(item.quantity for item in basket.items)
        if current_count > base.max_items:
            raise ValidationError(
                f"This basket has {current_count} items but the selected base "
                f"only holds {base.max_items}. Remove items first."
            )

        basket.base_id = base.id
        basket.base = base
        await self.db.flush()

        total = self._compute_total_in_memory(basket)
        return {"basket": basket, "running_total": total}

    async def add_item(self, basket_id: str, data: BasketItemAdd) -> dict:

        basket = await self._get_basket(basket_id)

        if not basket.base_id:
            raise ValidationError("Select a base container before adding items.")

        base = basket.base

        product = await self.product_repo.get_by_id(data.product_id)
        if not product:
            raise NotFoundError("Product", data.product_id)
        if product.is_sold_out:
            raise ValidationError(f"'{product.title}' is currently sold out.")

        current_count = sum(item.quantity for item in basket.items)
        if current_count + data.quantity > base.max_items:
            remaining = base.max_items - current_count
            raise ValidationError(
                f"Basket capacity exceeded. You can add {remaining} more item(s)."
            )

        new_item = await self.item_repo.create({
            "basket_id": basket_id,
            "product_id": data.product_id,
            "quantity": data.quantity,
        })

        new_item.product = product
        basket.items.append(new_item)

        total = self._compute_total_in_memory(basket)
        return {"basket": basket, "running_total": total}

    async def sync_items(self, basket_id: str, data: BasketItemsSync) -> dict:

        basket = await self.basket_repo.get_with_base(basket_id)
        if not basket:
            raise NotFoundError("Basket", basket_id)

        if not basket.base_id or not basket.base:
            raise ValidationError("Select a base container before adding items.")

        normalized: dict[str, int] = {}
        for item in data.items:
            normalized[item.product_id] = normalized.get(item.product_id, 0) + item.quantity

        if not normalized:
            raise ValidationError("Select at least one product with quantity.")

        total_quantity = sum(normalized.values())
        if total_quantity > basket.base.max_items:
            raise ValidationError(
                f"Basket capacity exceeded. Maximum allowed is {basket.base.max_items} item(s)."
            )

        product_ids = list(normalized.keys())
        products = await self.product_repo.get_by_ids(product_ids)
        products_by_id = {product.id: product for product in products}

        missing = [pid for pid in product_ids if pid not in products_by_id]
        if missing:
            raise NotFoundError("Product", missing[0])

        sold_out_titles = [
            product.title
            for product in products
            if product.is_sold_out
        ]
        if sold_out_titles:
            raise ValidationError(
                f"These products are sold out: {', '.join(sold_out_titles)}"
            )

        payload = [
            {
                "product_id": product_id,
                "quantity": quantity,
            }
            for product_id, quantity in normalized.items()
        ]
        await self.item_repo.replace_items(basket_id, payload)

        basket = await self.basket_repo.get_with_items(basket_id)
        total = self._compute_total_in_memory(basket)
        return {"basket": basket, "running_total": total}

    async def remove_item(self, basket_id: str, item_id: str) -> dict:

        item = await self.item_repo.get_by_id(item_id)
        if not item or item.basket_id != basket_id:
            raise NotFoundError("BasketItem", item_id)

        await self.item_repo.delete(item_id)

        basket = await self.basket_repo.get_with_items(basket_id)
        total = self._compute_total_in_memory(basket)
        return {"basket": basket, "running_total": total}

    async def get_basket_summary(self, basket_id: str) -> dict:

        basket = await self.basket_repo.get_with_items(basket_id)
        if not basket:
            raise NotFoundError("Basket", basket_id)

        total = self._compute_total_in_memory(basket)
        return {"basket": basket, "running_total": total}

    async def complete_basket(self, basket_id: str) -> dict:

        basket = await self._get_basket(basket_id)
        if not basket.base_id:
            raise ValidationError("Cannot complete: no base container selected.")

        item_count = sum(item.quantity for item in basket.items)
        if item_count == 0:
            raise ValidationError("Cannot complete: basket has no items.")

        basket.status = "complete"
        await self.db.flush()

        total = self._compute_total_in_memory(basket)
        return {"basket": basket, "running_total": total}

    async def quick_buy(
        self,
        user_id: Optional[str],
        data: QuickBuyRequest,
    ) -> dict:

        base = await self.base_repo.get_by_id(data.base_id)
        if not base:
            raise NotFoundError("GiftBase", data.base_id)

        product_ids = list({item.product_id for item in data.items})
        products = await self.product_repo.get_by_ids(product_ids)
        products_by_id = {p.id: p for p in products}

        missing = [pid for pid in product_ids if pid not in products_by_id]
        if missing:
            raise NotFoundError("Product", missing[0])

        normalized: dict[str, int] = {}
        for item in data.items:
            normalized[item.product_id] = normalized.get(item.product_id, 0) + item.quantity

        total_qty = sum(normalized.values())
        if total_qty > base.max_items:
            raise ValidationError(
                f"Too many items ({total_qty}) for this base (max {base.max_items})."
            )

        basket = await self.basket_repo.create({
            "user_id": user_id,
            "session_id": data.session_id,
            "base_id": base.id,
            "status": "complete",
        })

        new_items = []
        for product_id, quantity in normalized.items():
            item = BasketItem(
                basket_id=basket.id,
                product_id=product_id,
                quantity=quantity,
            )
            self.db.add(item)
            new_items.append(item)
        await self.db.flush()

        for item in new_items:
            set_committed_value(item, "product", products_by_id[item.product_id])

        if data.personalization:
            p = data.personalization
            if p.gift_message or p.ribbon_color or p.requested_delivery_date:
                pers = Personalization(
                    basket_id=basket.id,
                    gift_message=p.gift_message or "",
                    ribbon_color=p.ribbon_color or "",
                    requested_delivery_date=p.requested_delivery_date,
                )
                self.db.add(pers)
                await self.db.flush()

        cart_repo = CartRepository(self.db)
        cart_item_repo = CartItemRepository(self.db)
        cart = await cart_repo.get_or_create(
            user_id=user_id, session_id=data.session_id
        )
        await cart_item_repo.create({
            "cart_id": cart.id,
            "basket_id": basket.id,
            "quantity": 1,
        })

        set_committed_value(basket, "base", base)
        set_committed_value(basket, "items", new_items)

        base_price = float(base.price)
        items_total = sum(
            float(products_by_id[pid].price) * qty
            for pid, qty in normalized.items()
        )
        total = round(base_price + items_total, 2)

        return {"basket": basket, "running_total": total}

    async def complete_and_add_to_cart(
        self,
        basket_id: str,
        user_id: Optional[str],
        session_id: Optional[str],
        data: CompleteAndCartRequest,
    ) -> dict:

        basket = await self._get_basket(basket_id)

        if not basket.base_id:
            raise ValidationError("Cannot complete: no base container selected.")
        item_count = sum(item.quantity for item in basket.items)
        if item_count == 0:
            raise ValidationError("Cannot complete: basket has no items.")

        if data.personalization:
            p = data.personalization
            has_values = p.gift_message or p.ribbon_color or p.requested_delivery_date
            if has_values:

                existing_basket = await self.basket_repo.get_with_personalization(basket_id)
                if existing_basket and existing_basket.personalization:
                    pers = existing_basket.personalization
                    if p.gift_message is not None:
                        pers.gift_message = p.gift_message
                    if p.ribbon_color is not None:
                        pers.ribbon_color = p.ribbon_color
                    if p.requested_delivery_date is not None:
                        pers.requested_delivery_date = p.requested_delivery_date
                else:
                    pers = Personalization(
                        basket_id=basket_id,
                        gift_message=p.gift_message or "",
                        ribbon_color=p.ribbon_color or "",
                        requested_delivery_date=p.requested_delivery_date,
                    )
                    self.db.add(pers)
                await self.db.flush()

        basket.status = "complete"
        await self.db.flush()

        cart_repo = CartRepository(self.db)
        cart_item_repo = CartItemRepository(self.db)
        cart = await cart_repo.get_or_create(
            user_id=user_id, session_id=session_id
        )
        await cart_item_repo.create({
            "cart_id": cart.id,
            "basket_id": basket_id,
            "quantity": 1,
        })

        total = self._compute_total_in_memory(basket)
        return {"basket": basket, "running_total": total}

    async def list_bases(self) -> List[GiftBase]:

        return await self.base_repo.get_all()

    async def create_base(self, data: dict) -> GiftBase:

        return await self.base_repo.create(data)

    async def _get_basket(self, basket_id: str) -> Basket:

        basket = await self.basket_repo.get_with_items(basket_id)
        if not basket:
            raise NotFoundError("Basket", basket_id)
        return basket

    @staticmethod
    def _compute_total_in_memory(basket: Basket) -> float:

        base_price = float(basket.base.price) if basket.base else 0.0
        items_total = sum(
            float(item.product.price) * item.quantity
            for item in basket.items
            if item.product
        )
        return round(base_price + items_total, 2)