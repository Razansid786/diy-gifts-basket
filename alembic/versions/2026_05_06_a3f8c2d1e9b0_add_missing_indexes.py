"""add missing indexes for products, addresses, order_items

Revision ID: a3f8c2d1e9b0
Revises: 6df4b7f3e71d
Create Date: 2026-05-06 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op


revision: str = "a3f8c2d1e9b0"
down_revision: Union[str, None] = "6df4b7f3e71d"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_index("ix_products_is_active", "products", ["is_active"], unique=False)
    op.create_index("ix_products_category_id", "products", ["category_id"], unique=False)
    op.create_index("ix_addresses_user_id", "addresses", ["user_id"], unique=False)
    op.create_index("ix_order_items_order_id", "order_items", ["order_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_order_items_order_id", table_name="order_items")
    op.drop_index("ix_addresses_user_id", table_name="addresses")
    op.drop_index("ix_products_category_id", table_name="products")
    op.drop_index("ix_products_is_active", table_name="products")
