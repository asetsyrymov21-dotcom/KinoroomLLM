from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_session
from app.schemas.stock import (
    HallInventoryItem,
    StockBalanceRead,
    StockMovementRead,
    StockReceiveRequest,
)
from app.repositories.stock import StockMovementRepository
from app.services.stock import StockService

router = APIRouter(prefix="/stock", tags=["Stock"])


@router.post("/receive", response_model=StockBalanceRead, status_code=201)
async def receive_stock(
    data: StockReceiveRequest,
    session: AsyncSession = Depends(get_session),
):
    """
    Загрузить товар в зал (приход).
    Создаёт StockLocation если нет, обновляет баланс, логирует движение.
    """
    svc = StockService(session)
    return await svc.receive(data)


@router.get("/halls/{hall_id}/inventory", response_model=list[HallInventoryItem])
async def hall_inventory(
    hall_id: int,
    session: AsyncSession = Depends(get_session),
):
    """Инвентарь зала: остатки, резервы, доступно."""
    svc = StockService(session)
    return await svc.get_hall_inventory(hall_id)


@router.get(
    "/halls/{hall_id}/products/{product_id}/balance",
    response_model=StockBalanceRead,
)
async def product_balance(
    hall_id: int,
    product_id: int,
    session: AsyncSession = Depends(get_session),
):
    """Баланс конкретного товара в зале."""
    svc = StockService(session)
    return await svc.get_balance(hall_id, product_id)


@router.get("/halls/{hall_id}/movements", response_model=list[StockMovementRead])
async def hall_movements(
    hall_id: int,
    session: AsyncSession = Depends(get_session),
):
    """История движений склада зала."""
    repo = StockMovementRepository(session)
    return await repo.get_by_hall(hall_id)
