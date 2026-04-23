from datetime import datetime

from sqlalchemy import and_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.booking import Booking, BookingStatus
from app.models.order import Order, OrderItem
from app.repositories.base import TenantScopedRepository


class BookingRepository(TenantScopedRepository[Booking]):
    def __init__(self, session: AsyncSession, tenant_id: int) -> None:
        super().__init__(Booking, session, tenant_id)

    async def get_with_user(self, id: int) -> Booking | None:
        result = await self.session.execute(
            select(Booking)
            .options(selectinload(Booking.user))
            .where(
                Booking.id == id,
                Booking.tenant_id == self.tenant_id,
            )
        )
        return result.scalar_one_or_none()

    async def get_with_orders(self, id: int) -> Booking | None:
        result = await self.session.execute(
            select(Booking)
            .options(selectinload(Booking.orders))
            .where(
                Booking.id == id,
                Booking.tenant_id == self.tenant_id,
            )
        )
        return result.scalar_one_or_none()

    async def get_active_for_hall(self, hall_id: int) -> list[Booking]:
        result = await self.session.execute(
            select(Booking).where(
                Booking.tenant_id == self.tenant_id,
                Booking.hall_id == hall_id,
                Booking.status.in_([BookingStatus.pending, BookingStatus.active]),
            )
        )
        return list(result.scalars().all())

    async def has_overlap(
        self,
        hall_id: int,
        start_time: datetime,
        end_time: datetime,
        exclude_id: int | None = None,
    ) -> bool:
        """Проверяет, есть ли пересечение по времени для данного зала."""
        q = select(Booking).where(
            Booking.tenant_id == self.tenant_id,
            Booking.hall_id == hall_id,
            Booking.status.in_([BookingStatus.pending, BookingStatus.active]),
            or_(
                and_(Booking.start_time < end_time, Booking.end_time > start_time),
            ),
        )
        if exclude_id is not None:
            q = q.where(Booking.id != exclude_id)
        result = await self.session.execute(q)
        return result.scalar_one_or_none() is not None

    async def get_slots_for_date(self, hall_id: int, date_str: str) -> list[Booking]:
        """Брони зала (pending/active) на указанную дату."""
        d = datetime.strptime(date_str, "%Y-%m-%d")
        day_start = d.replace(hour=0, minute=0, second=0, microsecond=0)
        day_end = d.replace(hour=23, minute=59, second=59, microsecond=999999)
        result = await self.session.execute(
            select(Booking).where(
                Booking.tenant_id == self.tenant_id,
                Booking.hall_id == hall_id,
                Booking.status.in_([BookingStatus.pending, BookingStatus.active]),
                Booking.start_time < day_end,
                Booking.end_time > day_start,
            )
        )
        return list(result.scalars().all())

    async def get_by_user(self, user_id: int) -> list[Booking]:
        result = await self.session.execute(
            select(Booking)
            .where(
                Booking.tenant_id == self.tenant_id,
                Booking.user_id == user_id,
            )
            .order_by(Booking.created_at.desc())
        )
        return list(result.scalars().all())

    async def get_all(self) -> list[Booking]:
        result = await self.session.execute(
            select(Booking)
            .options(selectinload(Booking.user))
            .where(Booking.tenant_id == self.tenant_id)
            .order_by(Booking.created_at.desc())
        )
        return list(result.scalars().all())

    async def get_by_status(self, status: BookingStatus) -> list[Booking]:
        result = await self.session.execute(
            select(Booking)
            .options(selectinload(Booking.user))
            .where(
                Booking.tenant_id == self.tenant_id,
                Booking.status == status,
            )
            .order_by(Booking.start_time.asc())
        )
        return list(result.scalars().all())

    async def get_completed_with_details(self) -> list[Booking]:
        """Все завершённые брони с залом, заказами, позициями и продуктами."""
        result = await self.session.execute(
            select(Booking)
            .options(
                selectinload(Booking.hall),
                selectinload(Booking.orders).selectinload(Order.items).selectinload(OrderItem.product),
            )
            .where(
                Booking.tenant_id == self.tenant_id,
                Booking.status == BookingStatus.completed,
            )
            .order_by(Booking.completed_at.desc())
        )
        return list(result.scalars().all())

    async def get_one_with_details(self, booking_id: int) -> Booking | None:
        """Одна бронь со всеми деталями (для страницы сеанса)."""
        result = await self.session.execute(
            select(Booking)
            .options(
                selectinload(Booking.hall),
                selectinload(Booking.orders).selectinload(Order.items).selectinload(OrderItem.product),
            )
            .where(
                Booking.id == booking_id,
                Booking.tenant_id == self.tenant_id,
            )
        )
        return result.scalar_one_or_none()
