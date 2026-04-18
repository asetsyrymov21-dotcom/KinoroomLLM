"""stock_movements: add ON DELETE CASCADE for product_id and hall_id

Revision ID: 006
Revises: 005
Create Date: 2026-04-15
"""
from alembic import op

revision = "006"
down_revision = "005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # stock_movements.product_id → CASCADE
    op.drop_constraint(
        "stock_movements_product_id_fkey", "stock_movements", type_="foreignkey"
    )
    op.create_foreign_key(
        "stock_movements_product_id_fkey",
        "stock_movements", "products",
        ["product_id"], ["id"],
        ondelete="CASCADE",
    )

    # stock_movements.hall_id → CASCADE
    op.drop_constraint(
        "stock_movements_hall_id_fkey", "stock_movements", type_="foreignkey"
    )
    op.create_foreign_key(
        "stock_movements_hall_id_fkey",
        "stock_movements", "halls",
        ["hall_id"], ["id"],
        ondelete="CASCADE",
    )


def downgrade() -> None:
    op.drop_constraint(
        "stock_movements_product_id_fkey", "stock_movements", type_="foreignkey"
    )
    op.create_foreign_key(
        "stock_movements_product_id_fkey",
        "stock_movements", "products",
        ["product_id"], ["id"],
    )

    op.drop_constraint(
        "stock_movements_hall_id_fkey", "stock_movements", type_="foreignkey"
    )
    op.create_foreign_key(
        "stock_movements_hall_id_fkey",
        "stock_movements", "halls",
        ["hall_id"], ["id"],
    )
