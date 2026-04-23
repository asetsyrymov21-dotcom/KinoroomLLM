from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.hall import Hall
from app.repositories.base import TenantScopedRepository


class HallRepository(TenantScopedRepository[Hall]):
    def __init__(self, session: AsyncSession, tenant_id: int) -> None:
        super().__init__(Hall, session, tenant_id)

    async def get_active(self) -> list[Hall]:
        result = await self.session.execute(
            select(Hall).where(
                Hall.tenant_id == self.tenant_id,
                Hall.is_active.is_(True),
            )
        )
        return list(result.scalars().all())

    async def get_by_name(self, name: str) -> Hall | None:
        result = await self.session.execute(
            select(Hall).where(
                Hall.tenant_id == self.tenant_id,
                Hall.name == name,
            )
        )
        return result.scalar_one_or_none()
