from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_session
from app.models.booking import BookingStatus
from app.schemas.booking import BookingCreate, BookingRead, ExtraChargeRequest, SessionHistoryRead
from app.services.booking import BookingService

router = APIRouter(prefix="/bookings", tags=["Bookings"])


@router.get("/", response_model=list[BookingRead])
async def list_bookings(
    status: BookingStatus | None = Query(None, description="Фильтр по статусу"),
    session: AsyncSession = Depends(get_session),
):
    """
    Список всех броней.
    Опционально фильтровать по статусу: pending | active | completed | cancelled.
    Используется экраном оператора.
    """
    svc = BookingService(session)
    if status is not None:
        return await svc.list_by_status(status)
    return await svc.list_all()


@router.post("/", response_model=BookingRead, status_code=201)
async def create_booking(
    data: BookingCreate,
    session: AsyncSession = Depends(get_session),
):
    """
    Создать бронь.
    Проверяет доступность зала и отсутствие пересечений.
    """
    svc = BookingService(session)
    return await svc.create(data)


# ── Статичные маршруты ПЕРЕД /{booking_id} ──────────────────────────────────
# ВАЖНО: FastAPI матчит роуты сверху вниз. /history и /user/{id} должны
# стоять выше /{booking_id}, иначе "history" попытается стать int и упадёт.

@router.get("/halls/{hall_id}/slots")
async def get_hall_slots(
    hall_id: int,
    date: str = Query(..., description="Дата в формате YYYY-MM-DD"),
    session: AsyncSession = Depends(get_session),
):
    """Занятые временные слоты зала на дату (pending + active брони)."""
    svc = BookingService(session)
    return await svc.get_slots(hall_id, date)


@router.get("/history", response_model=list[SessionHistoryRead])
async def sessions_history(
    session: AsyncSession = Depends(get_session),
):
    """
    История завершённых сеансов.
    Возвращает все completed брони с полным составом заказов.
    """
    svc = BookingService(session)
    return await svc.get_history()


@router.get("/user/{user_id}", response_model=list[BookingRead])
async def list_user_bookings(
    user_id: int,
    session: AsyncSession = Depends(get_session),
):
    svc = BookingService(session)
    return await svc.list_by_user(user_id)


# ── Параметрические маршруты ─────────────────────────────────────────────────

@router.get("/{booking_id}", response_model=BookingRead)
async def get_booking(
    booking_id: int,
    session: AsyncSession = Depends(get_session),
):
    svc = BookingService(session)
    return await svc.get_or_404(booking_id)


@router.get("/{booking_id}/summary", response_model=SessionHistoryRead)
async def session_summary(
    booking_id: int,
    session: AsyncSession = Depends(get_session),
):
    """Детальная сводка одного сеанса (любого статуса)."""
    svc = BookingService(session)
    return await svc.get_session_summary(booking_id)


@router.post("/{booking_id}/activate", response_model=BookingRead)
async def activate_booking(
    booking_id: int,
    session: AsyncSession = Depends(get_session),
):
    """Перевести бронь в active (сеанс начался)."""
    svc = BookingService(session)
    return await svc.activate(booking_id)


@router.post("/{booking_id}/complete", response_model=BookingRead)
async def complete_booking(
    booking_id: int,
    session: AsyncSession = Depends(get_session),
):
    """Завершить сеанс."""
    svc = BookingService(session)
    return await svc.complete(booking_id)


@router.post("/{booking_id}/add-charge", response_model=BookingRead)
async def add_extra_charge(
    booking_id: int,
    data: ExtraChargeRequest,
    session: AsyncSession = Depends(get_session),
):
    """Добавить доплату к активному сеансу (например, за дополнительного человека)."""
    svc = BookingService(session)
    return await svc.add_extra_charge(booking_id, data.amount)


@router.post("/{booking_id}/cancel", response_model=BookingRead)
async def cancel_booking(
    booking_id: int,
    session: AsyncSession = Depends(get_session),
):
    """Отменить бронь."""
    svc = BookingService(session)
    return await svc.cancel(booking_id)
