"""add address, phone, logo_url to tenants

Revision ID: 010
Revises: 009
Create Date: 2026-04-25
"""
from alembic import op
import sqlalchemy as sa

revision = '010'
down_revision = '009'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('tenants', sa.Column('address', sa.String(500), nullable=True))
    op.add_column('tenants', sa.Column('phone', sa.String(50), nullable=True))
    op.add_column('tenants', sa.Column('logo_url', sa.String(1000), nullable=True))


def downgrade() -> None:
    op.drop_column('tenants', 'logo_url')
    op.drop_column('tenants', 'phone')
    op.drop_column('tenants', 'address')
