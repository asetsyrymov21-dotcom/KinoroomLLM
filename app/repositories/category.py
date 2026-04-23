from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.category import Category
from app.repositories.base import TenantScopedRepository


class CategoryRepository(TenantScopedRepository[Category]):
    def __init__(self, session: AsyncSession, tenant_id: int) -> None:
        super().__init__(Category, session, tenant_id)

    async def get_by_name(self, name: str) -> Category | None:
        result = await self.session.execute(
            select(Category).where(
                Category.tenant_id == self.tenant_id,
                Category.name == name,
            )
        )
        return result.scalar_one_or_none()

    async def list_active(self) -> list[Category]:
        result = await self.session.execute(
            select(Category)
            .where(
                Category.tenant_id == self.tenant_id,
                Category.is_active.is_(True),
            )
            .order_by(Category.position, Category.name)
        )
        return list(result.scalars().all())

    async def list_all(self) -> list[Category]:
        result = await self.session.execute(
            select(Category)
            .where(Category.tenant_id == self.tenant_id)
            .order_by(Category.position, Category.name)
        )
        return list(result.scalars().all())
