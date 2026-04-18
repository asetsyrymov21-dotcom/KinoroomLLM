from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.booking import Booking, BookingStatus
from app.models.loyalty import LoyaltyRule
from app.repositories.base import BaseRepository


class LoyaltyRepository(BaseRepository[LoyaltyRule]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(LoyaltyRule, session)

    async def list_active(self) -> list[LoyaltyRule]:
        result = await self.session.execute(
            select(LoyaltyRule)
            .where(LoyaltyRule.is_active.is_(True))
            .order_by(LoyaltyRule.visits_required)
        )
        return list(result.scalars().all())

    async def list_all(self) -> list[LoyaltyRule]:
        result = await self.session.execute(
            select(LoyaltyRule).order_by(LoyaltyRule.visits_required)
        )
        return list(result.scalars().all())

    async def count_completed_visits(self, user_id: int) -> int:
        """Количество завершённых бронирований пользователя."""
        result = await self.session.execute(
            select(func.count(Booking.id)).where(
                Booking.user_id == user_id,
                Booking.status == BookingStatus.completed,
            )
        )
        return result.scalar_one() or 0
