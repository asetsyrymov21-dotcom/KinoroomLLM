"""
FLOW 1: Бронирование зала
  pending → active → completed
                   → cancelled
"""
from datetime import datetime, timedelta, timezone
from decimal import Decimal

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.booking import Booking, BookingStatus
from app.repositories.booking import BookingRepository
from app.repositories.hall import HallRepository
from app.schemas.booking import (
    BookingCreate,
    SessionHistoryItem,
    SessionHistoryOrder,
    SessionHistoryRead,
)
from app.services.loyalty import LoyaltyService


class BookingService:
    def __init__(self, session: AsyncSession, tenant_id: int) -> None:
        self.session = session
        self.tenant_id = tenant_id
        self.repo = BookingRepository(session, tenant_id)
        self.hall_repo = HallRepository(session, tenant_id)

    async def create(self, data: BookingCreate) -> Booking:
        # Зал существует и активен (в рамках тенанта)
        hall = await self.hall_repo.get(data.hall_id)
        if hall is None or not hall.is_active:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Hall {data.hall_id} not found or inactive",
            )

        # Нет пересечений по времени
        overlap = await self.repo.has_overlap(
            hall_id=data.hall_id,
            start_time=data.start_time,
            end_time=data.end_time,
        )
        if overlap:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Hall is already booked for this time slot",
            )

        # Подсчитать стоимость (часы × цена)
        duration_hours = (
            data.end_time - data.start_time
        ).total_seconds() / 3600
        base_price = Decimal(str(round(duration_hours, 4))) * hall.price_per_hour
        base_price = round(base_price, 2)

        # Применить лояльность (только для фиксированных бронирований)
        total_price = base_price
        discount_pct = None
        if not data.is_open_ended:
            loyalty_svc = LoyaltyService(self.session)
            total_price, discount_pct, _ = await loyalty_svc.apply_to_booking(
                user_id=data.user_id, base_price=base_price, tenant_id=self.tenant_id
            )

        booking = await self.repo.create(
            user_id=data.user_id,
            hall_id=data.hall_id,
            start_time=data.start_time,
            end_time=data.end_time,
            status=BookingStatus.pending,
            total_price=total_price if not data.is_open_ended else None,
            is_open_ended=data.is_open_ended,
            discount_pct=discount_pct,
        )
        # populate_existing=True в get_with_user гарантирует, что selectinload
        # применится даже для объекта, уже находящегося в identity map после flush().
        return await self.repo.get_with_user(booking.id)

    async def get_or_404(self, booking_id: int) -> Booking:
        booking = await self.repo.get_with_user(booking_id)
        if booking is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Booking {booking_id} not found",
            )
        return booking

    async def activate(self, booking_id: int) -> Booking:
        booking = await self.get_or_404(booking_id)
        if booking.status != BookingStatus.pending:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot activate booking with status '{booking.status}'",
            )
        now = datetime.now(timezone.utc)
        earliest_activation = booking.start_time - timedelta(minutes=30)
        if now < earliest_activation:
            minutes_left = int((earliest_activation - now).total_seconds() / 60)
            hours_left = minutes_left // 60
            mins_left = minutes_left % 60
            time_str = f"{hours_left} ч {mins_left} мин" if hours_left else f"{mins_left} мин"
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Слишком рано. Активация возможна за 30 минут до начала. До старта ещё {time_str}.",
            )
        booking.status = BookingStatus.active
        return booking

    async def complete(self, booking_id: int) -> Booking:
        booking = await self.get_or_404(booking_id)
        if booking.status != BookingStatus.active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot complete booking with status '{booking.status}'",
            )
        now = datetime.now(timezone.utc)
        booking.status = BookingStatus.completed
        booking.completed_at = now

        # Для "по факту" — считаем реальную стоимость по completed_at
        if booking.is_open_ended:
            hall = await self.hall_repo.get(booking.hall_id)
            if hall:
                actual_hours = (now - booking.start_time).total_seconds() / 3600
                booking.total_price = round(
                    Decimal(str(round(actual_hours, 4))) * hall.price_per_hour, 2
                )
            booking.end_time = now  # фактическое время окончания

        return booking

    async def add_extra_charge(self, booking_id: int, amount: Decimal) -> Booking:
        booking = await self.get_or_404(booking_id)
        if booking.status != BookingStatus.active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Доплату можно добавить только к активному сеансу",
            )
        booking.extra_charge = (booking.extra_charge or Decimal("0")) + amount
        return booking

    async def cancel(self, booking_id: int) -> Booking:
        booking = await self.get_or_404(booking_id)
        if booking.status in (BookingStatus.completed, BookingStatus.cancelled):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot cancel booking with status '{booking.status}'",
            )
        booking.status = BookingStatus.cancelled
        return booking

    async def get_slots(self, hall_id: int, date_str: str) -> list[dict]:
        """Занятые временные интервалы зала на дату (для фронтенда)."""
        bookings = await self.repo.get_slots_for_date(hall_id, date_str)
        return [
            {
                "start_time": b.start_time.isoformat(),
                "end_time": b.end_time.isoformat(),
            }
            for b in bookings
        ]

    async def list_by_user(self, user_id: int) -> list[Booking]:
        return await self.repo.get_by_user(user_id)

    async def list_all(self) -> list[Booking]:
        return await self.repo.get_all()

    async def list_by_status(self, status: BookingStatus) -> list[Booking]:
        return await self.repo.get_by_status(status)

    # ── История сеансов ──────────────────────────────────────────

    def _booking_to_summary(self, booking: Booking) -> SessionHistoryRead:
        """Конвертирует Booking (с подгруженными relations) в SessionHistoryRead."""
        # Реальная длительность: от start_time до completed_at (или end_time)
        end = booking.completed_at or booking.end_time
        duration_min = int((end - booking.start_time).total_seconds() / 60)

        hall_cost = booking.total_price or Decimal("0")
        extra_charge = booking.extra_charge or Decimal("0")
        food_total = Decimal("0")
        orders_out = []

        for order in (booking.orders or []):
            items_out = []
            order_total = Decimal("0")
            for item in (order.items or []):
                subtotal = item.price_at_order * item.quantity
                order_total += subtotal
                food_total += subtotal
                items_out.append(SessionHistoryItem(
                    product_name=item.product.name if item.product else f"Товар #{item.product_id}",
                    quantity=item.quantity,
                    price_at_order=item.price_at_order,
                    subtotal=subtotal,
                ))
            orders_out.append(SessionHistoryOrder(
                id=order.id,
                status=order.status,
                created_at=order.created_at,
                items=items_out,
                order_total=order_total,
            ))

        return SessionHistoryRead(
            booking_id=booking.id,
            hall_name=booking.hall.name if booking.hall else f"Зал #{booking.hall_id}",
            start_time=booking.start_time,
            end_time=booking.end_time,
            completed_at=booking.completed_at,
            duration_minutes=duration_min,
            hall_cost=hall_cost,
            extra_charge=extra_charge,
            orders=orders_out,
            food_total=food_total,
            grand_total=hall_cost + extra_charge + food_total,
        )

    async def get_history(self) -> list[SessionHistoryRead]:
        """Все завершённые сеансы с деталями."""
        bookings = await self.repo.get_completed_with_details()
        return [self._booking_to_summary(b) for b in bookings]

    async def get_session_summary(self, booking_id: int) -> SessionHistoryRead:
        """Один сеанс с деталями."""
        booking = await self.repo.get_one_with_details(booking_id)
        if booking is None:
            raise HTTPException(status_code=404, detail=f"Booking {booking_id} not found")
        return self._booking_to_summary(booking)
