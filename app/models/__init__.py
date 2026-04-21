"""
app/models/__init__.py
──────────────────────
Central import hub for all ORM models.

Importing everything here ensures Alembic's ``Base.metadata`` is fully
populated when auto-generating migrations.
"""

from app.models.user import User                          # noqa: F401
from app.models.address import Address                    # noqa: F401
from app.models.category import Category                  # noqa: F401
from app.models.product import Product, ProductRelation   # noqa: F401
from app.models.basket import GiftBase, Basket, BasketItem  # noqa: F401
from app.models.personalization import Personalization    # noqa: F401
from app.models.cart import Cart, CartItem                # noqa: F401
from app.models.order import Order, OrderItem             # noqa: F401
