from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.product import Product
from app.repositories.base import TenantScopedRepository


class ProductRepository(TenantScopedRepository[Product]):
    def __init__(self, session: AsyncSession, tenant_id: int) -> None:
        super().__init__(Product, session, tenant_id)

    async def get_active(self) -> list[Product]:
        result = await self.session.execute(
            select(Product).where(
                Product.tenant_id == self.tenant_id,
                Product.is_active.is_(True),
            )
        )
        return list(result.scalars().all())

    async def get_by_sku(self, sku: str) -> Product | None:
        result = await self.session.execute(
            select(Product).where(
                Product.tenant_id == self.tenant_id,
                Product.sku == sku,
            )
        )
        return result.scalar_one_or_none()
