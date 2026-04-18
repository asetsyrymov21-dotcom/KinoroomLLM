"""initial schema

Revision ID: 001
Revises:
Create Date: 2026-04-12
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # users
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("telegram_id", sa.BigInteger(), nullable=False, unique=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("phone", sa.String(20), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )

    # halls
    op.create_table(
        "halls",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False, unique=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("capacity", sa.Integer(), nullable=False, server_default="1"),
        sa.Column(
            "price_per_hour",
            sa.Numeric(10, 2),
            nullable=False,
            server_default="0",
        ),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
    )

    # products
    op.create_table(
        "products",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("sku", sa.String(100), nullable=True, unique=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column(
            "price", sa.Numeric(10, 2), nullable=False, server_default="0"
        ),
        sa.Column("unit", sa.String(20), nullable=False, server_default="шт"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
    )

    # bookings
    op.create_table(
        "bookings",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "user_id",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "hall_id",
            sa.Integer(),
            sa.ForeignKey("halls.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("start_time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("end_time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column("total_price", sa.Numeric(10, 2), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index("ix_bookings_hall_id_status", "bookings", ["hall_id", "status"])

    # orders
    op.create_table(
        "orders",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "booking_id",
            sa.Integer(),
            sa.ForeignKey("bookings.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_orders_booking_id_status", "orders", ["booking_id", "status"])

    # order_items
    op.create_table(
        "order_items",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "order_id",
            sa.Integer(),
            sa.ForeignKey("orders.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "product_id",
            sa.Integer(),
            sa.ForeignKey("products.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("quantity", sa.Integer(), nullable=False),
        sa.Column("price_at_order", sa.Numeric(10, 2), nullable=False),
    )

    # stock_locations
    op.create_table(
        "stock_locations",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "hall_id",
            sa.Integer(),
            sa.ForeignKey("halls.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "product_id",
            sa.Integer(),
            sa.ForeignKey("products.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.UniqueConstraint("hall_id", "product_id", name="uq_stock_location"),
    )

    # stock_balances
    op.create_table(
        "stock_balances",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "stock_location_id",
            sa.Integer(),
            sa.ForeignKey("stock_locations.id", ondelete="CASCADE"),
            nullable=False,
            unique=True,
        ),
        sa.Column("quantity", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "reserved_quantity", sa.Integer(), nullable=False, server_default="0"
        ),
    )

    # stock_movements
    op.create_table(
        "stock_movements",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "product_id",
            sa.Integer(),
            sa.ForeignKey("products.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "hall_id",
            sa.Integer(),
            sa.ForeignKey("halls.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("quantity", sa.Integer(), nullable=False),
        sa.Column("movement_type", sa.String(20), nullable=False),
        sa.Column("reference_type", sa.String(50), nullable=True),
        sa.Column("reference_id", sa.Integer(), nullable=True),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index(
        "ix_stock_movements_hall_id", "stock_movements", ["hall_id", "created_at"]
    )


def downgrade() -> None:
    op.drop_table("stock_movements")
    op.drop_table("stock_balances")
    op.drop_table("stock_locations")
    op.drop_table("order_items")
    op.drop_table("orders")
    op.drop_table("bookings")
    op.drop_table("products")
    op.drop_table("halls")
    op.drop_table("users")
