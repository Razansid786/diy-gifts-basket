"""add query performance indexes

Revision ID: 6c9d3a2b4f11
Revises: e1eea9accb78
Create Date: 2026-04-27 16:20:00.000000

"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "6c9d3a2b4f11"
down_revision: Union[str, None] = "e1eea9accb78"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_index("ix_baskets_user_id", "baskets", ["user_id"], unique=False)
    op.create_index("ix_baskets_session_id", "baskets", ["session_id"], unique=False)
    op.create_index("ix_baskets_base_id", "baskets", ["base_id"], unique=False)

    op.create_index("ix_basket_items_basket_id", "basket_items", ["basket_id"], unique=False)
    op.create_index("ix_basket_items_product_id", "basket_items", ["product_id"], unique=False)

    op.create_index("ix_carts_session_id", "carts", ["session_id"], unique=False)

    op.create_index("ix_cart_items_cart_id", "cart_items", ["cart_id"], unique=False)
    op.create_index("ix_cart_items_basket_id", "cart_items", ["basket_id"], unique=False)

    op.create_index("ix_orders_user_id", "orders", ["user_id"], unique=False)
    op.create_index("ix_orders_payment_ref", "orders", ["payment_ref"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_orders_payment_ref", table_name="orders")
    op.drop_index("ix_orders_user_id", table_name="orders")

    op.drop_index("ix_cart_items_basket_id", table_name="cart_items")
    op.drop_index("ix_cart_items_cart_id", table_name="cart_items")

    op.drop_index("ix_carts_session_id", table_name="carts")

    op.drop_index("ix_basket_items_product_id", table_name="basket_items")
    op.drop_index("ix_basket_items_basket_id", table_name="basket_items")

    op.drop_index("ix_baskets_base_id", table_name="baskets")
    op.drop_index("ix_baskets_session_id", table_name="baskets")
    op.drop_index("ix_baskets_user_id", table_name="baskets")
