from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.hall import Hall
from app.repositories.hall import HallRepository
from app.schemas.hall import HallCreate, HallUpdate


class HallService:
    def __init__(self, session: AsyncSession) -> None:
        self.repo = HallRepository(session)

    async def create(self, data: HallCreate) -> Hall:
        existing = await self.repo.get_by_name(data.name)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Hall with name '{data.name}' already exists",
            )
        return await self.repo.create(**data.model_dump())

    async def get_or_404(self, hall_id: int) -> Hall:
        hall = await self.repo.get(hall_id)
        if hall is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Hall {hall_id} not found",
            )
        return hall

    async def list_all(self) -> list[Hall]:
        return list(await self.repo.get_all())

    async def list_active(self) -> list[Hall]:
        return await self.repo.get_active()

    async def update(self, hall_id: int, data: HallUpdate) -> Hall:
        hall = await self.get_or_404(hall_id)
        for field, value in data.model_dump(exclude_none=True).items():
            setattr(hall, field, value)
        return hall

    async def delete(self, hall_id: int) -> None:
        hall = await self.get_or_404(hall_id)
        await self.repo.delete(hall)
