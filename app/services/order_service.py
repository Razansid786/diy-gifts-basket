"""
app/services/order_service.py
─────────────────────────────
Business logic for checkout and order management (FR22–FR30).

Handles:
* Checkout flow — validates shipping, simulates payment, creates order.
* Idempotency guard against duplicate orders (NFR4).
* Order confirmation email trigger (FR26).
* Admin order listing and status updates (FR28, FR30).
* Packing list generation (FR29).
"""

import json
import uuid
from typing import List, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError, ValidationError
from app.models.order import Order, OrderItem
from app.repositories.basket_repo import BasketRepository
from app.repositories.cart_repo import CartRepository
from app.repositories.order_repo import OrderRepository, OrderItemRepository
from app.repositories.product_repo import ProductRepository
from app.repositories.address_repo import AddressRepository
from app.schemas.order import CheckoutRequest, OrderStatusUpdate, PackingListItem, PackingListResponse
from app.services.cart_service import CartService
from app.utils.email import send_order_confirmation


class OrderService:
    """Orchestrates checkout, order tracking, and admin fulfillment."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.order_repo = OrderRepository(db)
        self.order_item_repo = OrderItemRepository(db)
        self.cart_repo = CartRepository(db)
        self.basket_repo = BasketRepository(db)
        self.product_repo = ProductRepository(db)
        self.address_repo = AddressRepository(db)
        self.cart_service = CartService(db)

    # ── Checkout (FR24, FR25, FR26) ──────────────────────────────────

    async def checkout(
        self,
        data: CheckoutRequest,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
    ) -> Order:
        """
        Place an order from the current cart contents.

        Steps:
        1. Validate shipping info (FR24) or use saved address.
        2. Calculate totals from cart.
        3. Simulate payment and generate reference (FR25).
        4. Create Order + OrderItem rows.
        5. Clear the cart.
        6. Trigger confirmation email (FR26).

        The payment_ref is used as an idempotency key — if an order
        with the same ref already exists, the existing order is
        returned instead of creating a duplicate (NFR4).
        """
        # 1. Resolve shipping address
        shipping_json = await self._resolve_shipping(data, user_id)

        # 2. Get cart totals
        cart_data = await self.cart_service.get_cart(
            user_id=user_id, session_id=session_id
        )
        cart = cart_data["cart"]

        if not cart.items:
            raise ValidationError("Cart is empty. Add baskets before checkout.")

        subtotal = cart_data["subtotal"]
        shipping_fee = cart_data["shipping_fee"]
        total = cart_data["total"]

        # 3. Simulate payment (FR25) — generate a unique reference
        payment_ref = f"PAY-{uuid.uuid4().hex[:12].upper()}"

        # Idempotency check (NFR4)
        existing = await self.order_repo.get_by_payment_ref(payment_ref)
        if existing:
            return existing

        # 4. Create order
        order = await self.order_repo.create({
            "user_id": user_id,
            "guest_email": data.guest_email,
            "shipping_address_json": shipping_json,
            "shipping_fee": shipping_fee,
            "subtotal": subtotal,
            "total": total,
            "status": "pending",
            "payment_ref": payment_ref,
        })

        # Create order items from cart items
        for cart_item in cart.items:
            basket = await self.basket_repo.get_with_items(cart_item.basket_id)
            if basket:
                basket_total = await self._basket_total(basket)
                await self.order_item_repo.create({
                    "order_id": order.id,
                    "basket_id": basket.id,
                    "unit_price": basket_total,
                    "quantity": cart_item.quantity,
                })

        # 5. Clear the cart
        for cart_item in cart.items:
            await self.db.delete(cart_item)
        await self.db.commit()

        # 6. Send confirmation email (FR26)
        recipient = data.guest_email if data.guest_email else None
        if user_id:
            from app.repositories.user_repo import UserRepository
            user_repo = UserRepository(self.db)
            user = await user_repo.get_by_id(user_id)
            if user:
                recipient = user.email

        if recipient:
            await send_order_confirmation(recipient, order)

        return await self.order_repo.get_with_items(order.id)

    # ── User order history (FR3) ─────────────────────────────────────

    async def get_user_orders(self, user_id: str) -> List[Order]:
        """Return all orders for a user, newest first."""
        return await self.order_repo.get_user_orders(user_id)

    async def get_order(self, order_id: str) -> Order:
        """Get a single order with items."""
        order = await self.order_repo.get_with_items(order_id)
        if not order:
            raise NotFoundError("Order", order_id)
        return order

    # ── Admin endpoints (FR28, FR29, FR30) ───────────────────────────

    async def list_all_orders(self, skip: int = 0, limit: int = 50) -> List[Order]:
        """Admin: return all orders sorted by date (FR28)."""
        return await self.order_repo.get_all_sorted(skip=skip, limit=limit)

    async def update_order_status(
        self, order_id: str, data: OrderStatusUpdate
    ) -> Order:
        """
        Admin: change order status (FR30).

        Valid transitions: pending → processing → shipped → delivered.
        """
        valid_statuses = {"pending", "processing", "shipped", "delivered"}
        if data.status not in valid_statuses:
            raise ValidationError(
                f"Invalid status. Must be one of: {', '.join(valid_statuses)}"
            )

        order = await self.order_repo.update(order_id, {"status": data.status})
        if not order:
            raise NotFoundError("Order", order_id)
        return order

    async def get_packing_list(self, order_id: str) -> List[PackingListResponse]:
        """
        Admin: generate a packing list for an order (FR29).

        Returns a list of packing lists — one per basket in the order.
        Each packing list includes the base, items, and personalization.
        """
        order = await self.order_repo.get_with_items(order_id)
        if not order:
            raise NotFoundError("Order", order_id)

        packing_lists = []

        for order_item in order.items:
            basket = await self.basket_repo.get_with_items(order_item.basket_id)
            if not basket:
                continue

            # Build item details
            items = []
            for bi in basket.items:
                product = await self.product_repo.get_by_id(bi.product_id)
                if product:
                    items.append(PackingListItem(
                        product_id=product.id,
                        product_title=product.title,
                        product_sku=product.sku,
                        quantity=bi.quantity,
                    ))

            # Personalization details
            pers = basket.personalization
            packing_lists.append(PackingListResponse(
                order_id=order.id,
                basket_id=basket.id,
                base_name=basket.base.name if basket.base else "N/A",
                base_size=basket.base.size if basket.base else "N/A",
                items=items,
                personalization_message=pers.gift_message if pers else None,
                ribbon_color=pers.ribbon_color if pers else None,
                gift_tag_image_url=pers.gift_tag_image_url if pers else None,
                requested_delivery_date=str(pers.requested_delivery_date) if pers and pers.requested_delivery_date else None,
            ))

        return packing_lists

    # ── Private helpers ──────────────────────────────────────────────

    async def _resolve_shipping(
        self, data: CheckoutRequest, user_id: Optional[str]
    ) -> str:
        """
        Build the shipping address JSON string (FR24).

        Either uses a saved address_id or the inline shipping fields.
        All required fields are validated by the Pydantic schema.
        """
        if data.address_id and user_id:
            address = await self.address_repo.get_by_id(data.address_id)
            if not address or address.user_id != user_id:
                raise NotFoundError("Address", data.address_id)
            return json.dumps({
                "line1": address.line1,
                "line2": address.line2 or "",
                "city": address.city,
                "state": address.state,
                "zip_code": address.zip_code,
                "country": address.country,
            })

        # Use inline shipping info
        return json.dumps(data.shipping.model_dump())

    async def _basket_total(self, basket) -> float:
        """Calculate the total price of a single basket."""
        total = 0.0
        if basket.base:
            total += float(basket.base.price)
        for item in basket.items:
            product = await self.product_repo.get_by_id(item.product_id)
            if product:
                total += float(product.price) * item.quantity
        return round(total, 2)
