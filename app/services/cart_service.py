"""
app/services/cart_service.py
────────────────────────────
Business logic for cart management (FR22, FR23).

Handles:
* Adding completed baskets to the cart.
* Editing item quantities (FR22).
* Calculating subtotal and shipping (FR23).
"""

from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError, ValidationError
from app.models.cart import Cart, CartItem
from app.repositories.basket_repo import BasketRepository
from app.repositories.cart_repo import CartRepository, CartItemRepository
from app.repositories.product_repo import ProductRepository
from app.schemas.cart import CartItemAdd, CartItemUpdate


# ── Shipping fee schedule (FR23) ─────────────────────────────────────
# Flat-rate shipping based on order subtotal tiers.
SHIPPING_TIERS = [
    (0,     50,   9.99),   # $0 – $49.99   → $9.99 shipping
    (50,    100,  5.99),   # $50 – $99.99  → $5.99 shipping
    (100,   None, 0.00),   # $100+         → Free shipping
]


def calculate_shipping_fee(subtotal: float) -> float:
    """
    Determine shipping cost based on flat-rate tiers (FR23).

    Returns the shipping fee for the given subtotal.
    """
    for low, high, fee in SHIPPING_TIERS:
        if high is None and subtotal >= low:
            return fee
        if high is not None and low <= subtotal < high:
            return fee
    return 9.99  # Fallback


class CartService:
    """Orchestrates cart operations."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.cart_repo = CartRepository(db)
        self.cart_item_repo = CartItemRepository(db)
        self.basket_repo = BasketRepository(db)
        self.product_repo = ProductRepository(db)

    async def get_cart(
        self, user_id: Optional[str] = None, session_id: Optional[str] = None
    ) -> dict:
        """
        Return the full cart with calculated totals.

        Returns a dict with: cart object, subtotal, shipping_fee, total.
        """
        cart = await self.cart_repo.get_or_create(
            user_id=user_id, session_id=session_id
        )

        subtotal = await self._calculate_subtotal(cart)
        shipping_fee = calculate_shipping_fee(subtotal)

        return {
            "cart": cart,
            "subtotal": round(subtotal, 2),
            "shipping_fee": round(shipping_fee, 2),
            "total": round(subtotal + shipping_fee, 2),
        }

    async def add_item(
        self,
        data: CartItemAdd,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
    ) -> dict:
        """
        Add a completed basket to the cart.

        Validates that the basket exists and is marked as 'complete'.
        """
        # Validate the basket
        basket = await self.basket_repo.get_with_items(data.basket_id)
        if not basket:
            raise NotFoundError("Basket", data.basket_id)
        if basket.status != "complete":
            raise ValidationError("Only completed baskets can be added to the cart.")

        cart = await self.cart_repo.get_or_create(
            user_id=user_id, session_id=session_id
        )

        await self.cart_item_repo.create({
            "cart_id": cart.id,
            "basket_id": data.basket_id,
            "quantity": data.quantity,
        })

        return await self.get_cart(user_id=user_id, session_id=session_id)

    async def update_item(
        self,
        item_id: str,
        data: CartItemUpdate,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
    ) -> dict:
        """Edit the quantity of a cart item (FR22)."""
        item = await self.cart_item_repo.get_by_id(item_id)
        if not item:
            raise NotFoundError("CartItem", item_id)

        await self.cart_item_repo.update(item_id, {"quantity": data.quantity})
        return await self.get_cart(user_id=user_id, session_id=session_id)

    async def remove_item(
        self,
        item_id: str,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
    ) -> dict:
        """Remove a line item from the cart."""
        if not await self.cart_item_repo.delete(item_id):
            raise NotFoundError("CartItem", item_id)
        return await self.get_cart(user_id=user_id, session_id=session_id)

    # ── Private helpers ──────────────────────────────────────────────

    async def _calculate_subtotal(self, cart: Cart) -> float:
        """
        Sum the total price of all baskets in the cart.

        For each cart item: basket_total × quantity.
        basket_total = base.price + Σ(product.price × item_qty).
        """
        subtotal = 0.0

        for cart_item in cart.items:
            basket = await self.basket_repo.get_with_items(cart_item.basket_id)
            if not basket:
                continue

            basket_price = 0.0

            # Base price
            if basket.base:
                basket_price += float(basket.base.price)

            # Item prices
            for bi in basket.items:
                product = await self.product_repo.get_by_id(bi.product_id)
                if product:
                    basket_price += float(product.price) * bi.quantity

            subtotal += basket_price * cart_item.quantity

        return subtotal
