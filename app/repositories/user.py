from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.repositories.base import BaseRepository


class UserRepository(BaseRepository[User]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(User, session)

    async def get_by_telegram_id(self, telegram_id: int) -> User | None:
        result = await self.session.execute(
            select(User).where(User.telegram_id == telegram_id)
        )
        return result.scalar_one_or_none()

    async def get_or_create(self, telegram_id: int, name: str, phone: str | None = None) -> User:
        user = await self.get_by_telegram_id(telegram_id)
        if user is None:
            user = await self.create(telegram_id=telegram_id, name=name, phone=phone)
        return user

    async def update_phone(self, user_id: int, phone: str) -> User | None:
        user = await self.get(user_id)
        if user is None:
            return None
        user.phone = phone
        await self.session.flush()
        await self.session.refresh(user)
        return user
