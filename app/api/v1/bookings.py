from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_session, resolve_tenant_id
from app.models.booking import BookingStatus
from app.models.staff import Staff
from app.schemas.booking import BookingCreate, BookingRead, ExtraChargeRequest, SessionHistoryRead
from app.services.auth import get_current_staff, require_admin
from app.services.booking import BookingService

router = APIRouter(prefix="/bookings", tags=["Bookings"])


@router.get("", response_model=list[BookingRead])
async def list_bookings(
    status: BookingStatus | None = Query(None, description="Фильтр по статусу"),
    session: AsyncSession = Depends(get_session),
    current: Staff = Depends(get_current_staff),
):
    """
    Список всех броней тенанта (из JWT).
    Опционально фильтровать по статусу: pending | active | completed | cancelled.
    Используется экраном оператора.
    """
    svc = BookingService(session, current.tenant_id)
    if status is not None:
        return await svc.list_by_status(status)
    return await svc.list_all()


@router.post("", response_model=BookingRead, status_code=201)
async def create_booking(
    data: BookingCreate,
    session: AsyncSession = Depends(get_session),
):
    """
    Создать бронь. tenant_id берётся из тела запроса (default=1 для совместимости).
    Проверяет доступность зала и отсутствие пересечений.
    """
    svc = BookingService(session, data.tenant_id)
    return await svc.create(data)


# ── Статичные маршруты ПЕРЕД /{booking_id} ──────────────────────────────────
# ВАЖНО: FastAPI матчит роуты сверху вниз. /history и /user/{id} должны
# стоять выше /{booking_id}, иначе "history" попытается стать int и упадёт.

@router.get("/halls/{hall_id}/slots")
async def get_hall_slots(
    hall_id: int,
    date: str = Query(..., description="Дата в формате YYYY-MM-DD"),
    tenant_id: int = Depends(resolve_tenant_id),
    session: AsyncSession = Depends(get_session),
):
    """Занятые временные слоты зала на дату (pending + active брони)."""
    svc = BookingService(session, tenant_id)
    return await svc.get_slots(hall_id, date)


@router.get("/history", response_model=list[SessionHistoryRead])
async def sessions_history(
    session: AsyncSession = Depends(get_session),
    current: Staff = Depends(get_current_staff),
):
    """
    История завершённых сеансов тенанта.
    Возвращает все completed брони с полным составом заказов.
    """
    svc = BookingService(session, current.tenant_id)
    return await svc.get_history()


@router.get("/user/{user_id}", response_model=list[BookingRead])
async def list_user_bookings(
    user_id: int,
    tenant_id: int = Depends(resolve_tenant_id),
    session: AsyncSession = Depends(get_session),
):
    svc = BookingService(session, tenant_id)
    return await svc.list_by_user(user_id)


# ── Параметрические маршруты ─────────────────────────────────────────────────

@router.get("/{booking_id}", response_model=BookingRead)
async def get_booking(
    booking_id: int,
    tenant_id: int = Depends(resolve_tenant_id),
    session: AsyncSession = Depends(get_session),
):
    svc = BookingService(session, tenant_id)
    return await svc.get_or_404(booking_id)


@router.get("/{booking_id}/summary", response_model=SessionHistoryRead)
async def session_summary(
    booking_id: int,
    session: AsyncSession = Depends(get_session),
    current: Staff = Depends(get_current_staff),
):
    """Детальная сводка одного сеанса (любого статуса)."""
    svc = BookingService(session, current.tenant_id)
    return await svc.get_session_summary(booking_id)


@router.post("/{booking_id}/activate", response_model=BookingRead)
async def activate_booking(
    booking_id: int,
    session: AsyncSession = Depends(get_session),
    current: Staff = Depends(get_current_staff),
):
    """Перевести бронь в active (сеанс начался)."""
    svc = BookingService(session, current.tenant_id)
    return await svc.activate(booking_id)


@router.post("/{booking_id}/complete", response_model=BookingRead)
async def complete_booking(
    booking_id: int,
    session: AsyncSession = Depends(get_session),
    current: Staff = Depends(get_current_staff),
):
    """Завершить сеанс."""
    svc = BookingService(session, current.tenant_id)
    return await svc.complete(booking_id)


@router.post("/{booking_id}/add-charge", response_model=BookingRead)
async def add_extra_charge(
    booking_id: int,
    data: ExtraChargeRequest,
    session: AsyncSession = Depends(get_session),
    current: Staff = Depends(get_current_staff),
):
    """Добавить доплату к активному сеансу (например, за дополнительного человека)."""
    svc = BookingService(session, current.tenant_id)
    return await svc.add_extra_charge(booking_id, data.amount)


@router.post("/{booking_id}/cancel", response_model=BookingRead)
async def cancel_booking(
    booking_id: int,
    session: AsyncSession = Depends(get_session),
    current: Staff = Depends(require_admin),
):
    """Отменить бронь. Только для admin."""
    svc = BookingService(session, current.tenant_id)
    return await svc.cancel(booking_id)
