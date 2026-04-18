"""categories, cost_price, loyalty_rules, discount_pct

Revision ID: 004
Revises: 003
Create Date: 2026-04-14
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "004"
down_revision: Union[str, None] = "003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── categories ─────────────────────────────────────────────────
    op.create_table(
        "categories",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(100), nullable=False, unique=True),
        sa.Column("emoji", sa.String(10), nullable=True),
        sa.Column("position", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
    )

    # ── products: category_id + cost_price ─────────────────────────
    op.add_column(
        "products",
        sa.Column(
            "category_id",
            sa.Integer(),
            sa.ForeignKey("categories.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )
    op.add_column(
        "products",
        sa.Column("cost_price", sa.Numeric(10, 2), nullable=True),
    )

    # ── loyalty_rules ───────────────────────────────────────────────
    op.create_table(
        "loyalty_rules",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("visits_required", sa.Integer(), nullable=False),
        sa.Column("reward_type", sa.String(30), nullable=False),  # discount | free_booking
        sa.Column("reward_value", sa.Numeric(5, 2), nullable=False, server_default="0"),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
    )

    # ── bookings: discount_pct ──────────────────────────────────────
    op.add_column(
        "bookings",
        sa.Column("discount_pct", sa.Numeric(5, 2), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("bookings", "discount_pct")
    op.drop_table("loyalty_rules")
    op.drop_column("products", "cost_price")
    op.drop_column("products", "category_id")
    op.drop_table("categories")
