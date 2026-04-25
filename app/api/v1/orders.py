from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_session
from app.models.staff import Staff
from app.schemas.order import OrderCreate, OrderItemAdd, OrderItemRead, OrderRead
from app.services.auth import get_current_staff
from app.services.order import OrderService

router = APIRouter(prefix="/orders", tags=["Orders"])


@router.get("", response_model=list[OrderRead])
async def list_orders(
    session: AsyncSession = Depends(get_session),
    current: Staff = Depends(get_current_staff),
):
    """Список всех заказов тенанта (из JWT). Для панели admin/operator."""
    from app.repositories.order import OrderRepository
    from sqlalchemy import select
    from app.models.order import Order
    result = await session.execute(
        select(Order)
        .where(Order.tenant_id == current.tenant_id)
        .order_by(Order.created_at.desc())
    )
    return list(result.scalars().all())


@router.post("", response_model=OrderRead, status_code=201)
async def create_order(
    data: OrderCreate,
    tenant_id: int = Query(1, description="ID тенанта"),
    session: AsyncSession = Depends(get_session),
):
    """
    Создать заказ для активной брони.
    Бронь должна иметь статус active или pending.
    tenant_id передаётся query-параметром (мини-апп) или берётся из JWT (оператор).
    """
    svc = OrderService(session, tenant_id)
    return await svc.create(data)


@router.get("/{order_id}", response_model=OrderRead)
async def get_order(
    order_id: int,
    session: AsyncSession = Depends(get_session),
    current: Staff = Depends(get_current_staff),
):
    svc = OrderService(session, current.tenant_id)
    return await svc.get_or_404(order_id)


@router.get("/booking/{booking_id}", response_model=list[OrderRead])
async def list_orders_by_booking(
    booking_id: int,
    tenant_id: int = Query(1, description="ID тенанта"),
    session: AsyncSession = Depends(get_session),
):
    """Все заказы по брони."""
    svc = OrderService(session, tenant_id)
    return await svc.list_by_booking(booking_id)


@router.get("/booking/{booking_id}/pending", response_model=list[OrderRead])
async def list_pending_orders(
    booking_id: int,
    session: AsyncSession = Depends(get_session),
    current: Staff = Depends(get_current_staff),
):
    """Висящие (pending) заказы — экран оператора."""
    svc = OrderService(session, current.tenant_id)
    return await svc.list_pending(booking_id)


@router.post("/{order_id}/items", response_model=OrderItemRead, status_code=201)
async def add_item(
    order_id: int,
    data: OrderItemAdd,
    tenant_id: int = Query(1, description="ID тенанта"),
    session: AsyncSession = Depends(get_session),
):
    """
    Добавить позицию в заказ.
    Автоматически резервирует товар на складе зала.
    """
    svc = OrderService(session, tenant_id)
    return await svc.add_item(order_id, data)


@router.post("/{order_id}/complete", response_model=OrderRead)
async def complete_order(
    order_id: int,
    session: AsyncSession = Depends(get_session),
    current: Staff = Depends(get_current_staff),
):
    """
    Оператор нажал «Выполнено».
    Списывает зарезервированный товар со склада.
    """
    svc = OrderService(session, current.tenant_id)
    return await svc.complete(order_id)


@router.post("/{order_id}/cancel", response_model=OrderRead)
async def cancel_order(
    order_id: int,
    session: AsyncSession = Depends(get_session),
    current: Staff = Depends(get_current_staff),
):
    """Отменить заказ — снять резервы."""
    svc = OrderService(session, current.tenant_id)
    return await svc.cancel(order_id)
