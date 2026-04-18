from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.product import Product
from app.repositories.base import BaseRepository


class ProductRepository(BaseRepository[Product]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(Product, session)

    async def get_active(self) -> list[Product]:
        result = await self.session.execute(
            select(Product).where(Product.is_active.is_(True))
        )
        return list(result.scalars().all())

    async def get_by_sku(self, sku: str) -> Product | None:
        result = await self.session.execute(
            select(Product).where(Product.sku == sku)
        )
        return result.scalar_one_or_none()
