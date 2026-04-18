from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.category import Category
from app.repositories.base import BaseRepository


class CategoryRepository(BaseRepository[Category]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(Category, session)

    async def get_by_name(self, name: str) -> Category | None:
        result = await self.session.execute(
            select(Category).where(Category.name == name)
        )
        return result.scalar_one_or_none()

    async def list_active(self) -> list[Category]:
        result = await self.session.execute(
            select(Category)
            .where(Category.is_active.is_(True))
            .order_by(Category.position, Category.name)
        )
        return list(result.scalars().all())

    async def list_all(self) -> list[Category]:
        result = await self.session.execute(
            select(Category).order_by(Category.position, Category.name)
        )
        return list(result.scalars().all())
