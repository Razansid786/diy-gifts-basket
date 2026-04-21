"""
app/services/basket_service.py
──────────────────────────────
Business logic for the step-by-step basket builder (FR11–FR17).

Core responsibilities:
* Create a new basket (FR11).
* Set / change the base container (FR12).
* Add items while enforcing capacity limits (FR14).
* Calculate the running total dynamically (FR13).
* Remove items (FR16).
* Produce a review summary (FR17).
"""

from typing import List, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError, ValidationError
from app.models.basket import Basket, BasketItem, GiftBase
from app.repositories.basket_repo import (
    BasketRepository,
    BasketItemRepository,
    GiftBaseRepository,
)
from app.repositories.product_repo import ProductRepository
from app.schemas.basket import BasketCreate, BasketItemAdd


class BasketService:
    """Orchestrates the basket builder wizard."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.basket_repo = BasketRepository(db)
        self.item_repo = BasketItemRepository(db)
        self.base_repo = GiftBaseRepository(db)
        self.product_repo = ProductRepository(db)

    # ── Step 1: Create basket (FR11) ─────────────────────────────────

    async def create_basket(
        self,
        user_id: Optional[str],
        data: BasketCreate,
    ) -> Basket:
        """
        Start a new basket build.

        If a ``base_id`` is provided, it is validated and set immediately.
        """
        create_data = {
            "user_id": user_id,
            "session_id": data.session_id,
            "base_id": None,
            "status": "draft",
        }

        if data.base_id:
            base = await self.base_repo.get_by_id(data.base_id)
            if not base:
                raise NotFoundError("GiftBase", data.base_id)
            create_data["base_id"] = base.id

        basket = await self.basket_repo.create(create_data)
        return await self.basket_repo.get_with_items(basket.id)

    # ── Step 1b: Select / change base (FR12) ─────────────────────────

    async def set_base(self, basket_id: str, base_id: str) -> Basket:
        """
        Assign or change the container for a basket.

        The base must be selected before items can be added (FR12).
        If changing to a smaller base, existing items that exceed
        the new capacity are *not* auto-removed — a validation error
        is raised instead.
        """
        basket = await self._get_basket(basket_id)
        base = await self.base_repo.get_by_id(base_id)
        if not base:
            raise NotFoundError("GiftBase", base_id)

        # Check that existing items fit in the new base
        current_count = await self.item_repo.count_items_in_basket(basket_id)
        if current_count > base.max_items:
            raise ValidationError(
                f"This basket has {current_count} items but the selected base "
                f"only holds {base.max_items}. Remove items first."
            )

        await self.basket_repo.update(basket_id, {"base_id": base.id})
        return await self.basket_repo.get_with_items(basket_id)

    # ── Step 2: Add items (FR14, FR15) ───────────────────────────────

    async def add_item(self, basket_id: str, data: BasketItemAdd) -> Basket:
        """
        Add a product to the basket.

        Enforces:
        * A base must be selected first (FR12).
        * Total item count must not exceed ``base.max_items`` (FR14).
        * The product must exist and be in stock.

        Raises
        ------
        ValidationError
            If capacity is exceeded or base is not selected.
        NotFoundError
            If the product does not exist.
        """
        basket = await self._get_basket(basket_id)

        # Base required
        if not basket.base_id:
            raise ValidationError("Select a base container before adding items.")

        base = await self.base_repo.get_by_id(basket.base_id)

        # Check product
        product = await self.product_repo.get_by_id(data.product_id)
        if not product:
            raise NotFoundError("Product", data.product_id)
        if product.is_sold_out:
            raise ValidationError(f"'{product.title}' is currently sold out.")

        # Check capacity (FR14)
        current_count = await self.item_repo.count_items_in_basket(basket_id)
        if current_count + data.quantity > base.max_items:
            remaining = base.max_items - current_count
            raise ValidationError(
                f"Basket capacity exceeded. You can add {remaining} more item(s)."
            )

        # Add item
        await self.item_repo.create({
            "basket_id": basket_id,
            "product_id": data.product_id,
            "quantity": data.quantity,
        })

        return await self.basket_repo.get_with_items(basket_id)

    # ── Remove item (FR16) ───────────────────────────────────────────

    async def remove_item(self, basket_id: str, item_id: str) -> Basket:
        """One-click removal of an item from the basket (FR16)."""
        item = await self.item_repo.get_by_id(item_id)
        if not item or item.basket_id != basket_id:
            raise NotFoundError("BasketItem", item_id)

        await self.item_repo.delete(item_id)
        return await self.basket_repo.get_with_items(basket_id)

    # ── View contents (FR15) & Review summary (FR17) ─────────────────

    async def get_basket_summary(self, basket_id: str) -> dict:
        """
        Build a summary dict with the basket, its items, and running total.

        The running total (FR13) = base price + sum(product.price × qty).
        """
        basket = await self.basket_repo.get_with_items(basket_id)
        if not basket:
            raise NotFoundError("Basket", basket_id)

        running_total = await self._calculate_running_total(basket)

        return {
            "basket": basket,
            "running_total": running_total,
        }

    # ── Mark as complete ─────────────────────────────────────────────

    async def complete_basket(self, basket_id: str) -> Basket:
        """
        Mark a basket as 'complete' so it can be added to the cart.

        Validates that the basket has a base and at least one item.
        """
        basket = await self._get_basket(basket_id)
        if not basket.base_id:
            raise ValidationError("Cannot complete: no base container selected.")

        item_count = await self.item_repo.count_items_in_basket(basket_id)
        if item_count == 0:
            raise ValidationError("Cannot complete: basket has no items.")

        await self.basket_repo.update(basket_id, {"status": "complete"})
        return await self.basket_repo.get_with_items(basket_id)

    # ── Gift base admin CRUD ─────────────────────────────────────────

    async def list_bases(self) -> List[GiftBase]:
        """Return all available gift bases / containers."""
        return await self.base_repo.get_all()

    async def create_base(self, data: dict) -> GiftBase:
        """Admin: add a new gift base type."""
        return await self.base_repo.create(data)

    # ── Private helpers ──────────────────────────────────────────────

    async def _get_basket(self, basket_id: str) -> Basket:
        """Fetch basket or raise NotFoundError."""
        basket = await self.basket_repo.get_with_items(basket_id)
        if not basket:
            raise NotFoundError("Basket", basket_id)
        return basket

    async def _calculate_running_total(self, basket: Basket) -> float:
        """
        Compute the running total price for a basket (FR13).

        Formula: base.price + Σ(product.price × item.quantity)
        """
        total = 0.0

        # Add base price
        if basket.base_id and basket.base:
            total += float(basket.base.price)

        # Add item prices
        for item in basket.items:
            product = await self.product_repo.get_by_id(item.product_id)
            if product:
                total += float(product.price) * item.quantity

        return round(total, 2)
