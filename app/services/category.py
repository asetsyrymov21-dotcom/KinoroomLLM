from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.category import Category
from app.repositories.category import CategoryRepository
from app.schemas.category import CategoryCreate, CategoryUpdate


class CategoryService:
    def __init__(self, session: AsyncSession, tenant_id: int) -> None:
        self.repo = CategoryRepository(session, tenant_id)

    async def create(self, data: CategoryCreate) -> Category:
        existing = await self.repo.get_by_name(data.name)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Category '{data.name}' already exists",
            )
        return await self.repo.create(**data.model_dump())

    async def get_or_404(self, category_id: int) -> Category:
        cat = await self.repo.get(category_id)
        if cat is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Category {category_id} not found",
            )
        return cat

    async def list_active(self) -> list[Category]:
        return await self.repo.list_active()

    async def list_all(self) -> list[Category]:
        return await self.repo.list_all()

    async def update(self, category_id: int, data: CategoryUpdate) -> Category:
        cat = await self.get_or_404(category_id)
        for field, value in data.model_dump(exclude_none=True).items():
            setattr(cat, field, value)
        return cat

    async def delete(self, category_id: int) -> None:
        cat = await self.get_or_404(category_id)
        await self.repo.delete(cat)
