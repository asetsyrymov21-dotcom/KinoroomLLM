from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_session
from app.schemas.order import OrderCreate, OrderItemAdd, OrderItemRead, OrderRead
from app.services.order import OrderService

router = APIRouter(prefix="/orders", tags=["Orders"])


@router.post("/", response_model=OrderRead, status_code=201)
async def create_order(
    data: OrderCreate,
    session: AsyncSession = Depends(get_session),
):
    """
    Создать заказ для активной брони.
    Бронь должна иметь статус active.
    """
    svc = OrderService(session)
    return await svc.create(data)


@router.get("/{order_id}", response_model=OrderRead)
async def get_order(
    order_id: int,
    session: AsyncSession = Depends(get_session),
):
    svc = OrderService(session)
    return await svc.get_or_404(order_id)


@router.get("/booking/{booking_id}", response_model=list[OrderRead])
async def list_orders_by_booking(
    booking_id: int,
    session: AsyncSession = Depends(get_session),
):
    """Все заказы по брони."""
    svc = OrderService(session)
    return await svc.list_by_booking(booking_id)


@router.get("/booking/{booking_id}/pending", response_model=list[OrderRead])
async def list_pending_orders(
    booking_id: int,
    session: AsyncSession = Depends(get_session),
):
    """Висящие (pending) заказы — экран оператора."""
    svc = OrderService(session)
    return await svc.list_pending(booking_id)


@router.post("/{order_id}/items", response_model=OrderItemRead, status_code=201)
async def add_item(
    order_id: int,
    data: OrderItemAdd,
    session: AsyncSession = Depends(get_session),
):
    """
    Добавить позицию в заказ.
    Автоматически резервирует товар на складе зала.
    """
    svc = OrderService(session)
    return await svc.add_item(order_id, data)


@router.post("/{order_id}/complete", response_model=OrderRead)
async def complete_order(
    order_id: int,
    session: AsyncSession = Depends(get_session),
):
    """
    Оператор нажал «Выполнено».
    Списывает зарезервированный товар со склада.
    """
    svc = OrderService(session)
    return await svc.complete(order_id)


@router.post("/{order_id}/cancel", response_model=OrderRead)
async def cancel_order(
    order_id: int,
    session: AsyncSession = Depends(get_session),
):
    """Отменить заказ — снять резервы."""
    svc = OrderService(session)
    return await svc.cancel(order_id)
