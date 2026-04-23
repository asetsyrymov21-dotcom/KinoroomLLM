from typing import Any, Generic, Sequence, Type, TypeVar

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import Base

ModelT = TypeVar("ModelT", bound=Base)


class BaseRepository(Generic[ModelT]):
    def __init__(self, model: Type[ModelT], session: AsyncSession) -> None:
        self.model = model
        self.session = session

    async def get(self, id: int) -> ModelT | None:
        return await self.session.get(self.model, id)

    async def get_all(self) -> Sequence[ModelT]:
        result = await self.session.execute(select(self.model))
        return result.scalars().all()

    async def create(self, **kwargs: Any) -> ModelT:
        obj = self.model(**kwargs)
        self.session.add(obj)
        await self.session.flush()
        await self.session.refresh(obj)
        return obj

    async def delete(self, obj: ModelT) -> None:
        await self.session.delete(obj)
        await self.session.flush()


class TenantScopedRepository(BaseRepository[ModelT]):
    """
    Базовый репозиторий с автоматической фильтрацией по tenant_id.
    Все операции get / get_all / create изолированы в рамках тенанта.
    """

    def __init__(self, model: Type[ModelT], session: AsyncSession, tenant_id: int) -> None:
        super().__init__(model, session)
        self.tenant_id = tenant_id

    async def get(self, id: int) -> ModelT | None:
        result = await self.session.execute(
            select(self.model).where(
                self.model.id == id,
                self.model.tenant_id == self.tenant_id,
            )
        )
        return result.scalar_one_or_none()

    async def get_all(self) -> Sequence[ModelT]:
        result = await self.session.execute(
            select(self.model).where(self.model.tenant_id == self.tenant_id)
        )
        return result.scalars().all()

    async def create(self, **kwargs: Any) -> ModelT:
        return await super().create(tenant_id=self.tenant_id, **kwargs)
