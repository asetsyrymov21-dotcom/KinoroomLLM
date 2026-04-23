"""add multitenancy: tenants table + tenant_id in all entities

Revision ID: 009
Revises: 008
Create Date: 2026-04-23
"""
import sqlalchemy as sa
from alembic import op

revision = '009'
down_revision = '008'
branch_labels = None
depends_on = None

# Таблицы, в которые добавляем tenant_id
TENANT_TABLES = [
    'halls',
    'bookings',
    'products',
    'categories',
    'orders',
    'order_items',
    'staff',
    'stock_locations',
    'stock_balances',
    'stock_movements',
]


def upgrade() -> None:
    # ── 1. Создаём таблицу tenants ────────────────────────────────────────────
    op.create_table(
        'tenants',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('slug', sa.String(100), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint('slug', name='uq_tenants_slug'),
    )

    # ── 2. Вставляем дефолтный тенант (id=1) для существующих данных ──────────
    op.execute(
        "INSERT INTO tenants (id, name, slug) VALUES (1, 'Default', 'default')"
    )

    # ── 3. Добавляем tenant_id в каждую таблицу ───────────────────────────────
    for table in TENANT_TABLES:
        # Добавить колонку nullable
        op.add_column(table, sa.Column('tenant_id', sa.Integer(), nullable=True))
        # Заполнить существующие строки дефолтным тенантом
        op.execute(f"UPDATE {table} SET tenant_id = 1")
        # Сделать NOT NULL
        op.alter_column(table, 'tenant_id', nullable=False)
        # Внешний ключ на tenants
        op.create_foreign_key(
            f'fk_{table}_tenant_id',
            table, 'tenants',
            ['tenant_id'], ['id'],
            ondelete='CASCADE',
        )
        # Индекс для быстрой фильтрации
        op.create_index(f'ix_{table}_tenant_id', table, ['tenant_id'])

    # ── 4. Обновляем уникальные ограничения ───────────────────────────────────

    # halls: убрать global unique на name, добавить per-tenant
    op.drop_constraint('halls_name_key', 'halls', type_='unique')
    op.create_unique_constraint(
        'uq_halls_tenant_name', 'halls', ['tenant_id', 'name']
    )

    # products: убрать global unique на sku, добавить per-tenant
    op.drop_constraint('products_sku_key', 'products', type_='unique')
    op.create_unique_constraint(
        'uq_products_tenant_sku', 'products', ['tenant_id', 'sku']
    )

    # categories: убрать global unique на name, добавить per-tenant
    op.drop_constraint('categories_name_key', 'categories', type_='unique')
    op.create_unique_constraint(
        'uq_categories_tenant_name', 'categories', ['tenant_id', 'name']
    )

    # staff: убрать global unique на username, добавить per-tenant
    op.drop_constraint('staff_username_key', 'staff', type_='unique')
    op.create_unique_constraint(
        'uq_staff_tenant_username', 'staff', ['tenant_id', 'username']
    )


def downgrade() -> None:
    # Восстанавливаем глобальные unique constraints
    op.drop_constraint('uq_staff_tenant_username', 'staff', type_='unique')
    op.create_unique_constraint('staff_username_key', 'staff', ['username'])

    op.drop_constraint('uq_categories_tenant_name', 'categories', type_='unique')
    op.create_unique_constraint('categories_name_key', 'categories', ['name'])

    op.drop_constraint('uq_products_tenant_sku', 'products', type_='unique')
    op.create_unique_constraint('products_sku_key', 'products', ['sku'])

    op.drop_constraint('uq_halls_tenant_name', 'halls', type_='unique')
    op.create_unique_constraint('halls_name_key', 'halls', ['name'])

    # Удаляем tenant_id из всех таблиц
    for table in reversed(TENANT_TABLES):
        op.drop_index(f'ix_{table}_tenant_id', table_name=table)
        op.drop_constraint(f'fk_{table}_tenant_id', table, type_='foreignkey')
        op.drop_column(table, 'tenant_id')

    # Удаляем таблицу tenants
    op.drop_table('tenants')
