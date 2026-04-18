"""
FLOW 3 (часть): Приход товара в зал + просмотр остатков
"""
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.stock import MovementType, StockBalance, StockLocation
from app.repositories.hall import HallRepository
from app.repositories.product import ProductRepository
from app.repositories.stock import (
    StockBalanceRepository,
    StockLocationRepository,
    StockMovementRepository,
)
from app.schemas.stock import HallInventoryItem, StockReceiveRequest


class StockService:
    def __init__(self, session: AsyncSession) -> None:
        self.loc_repo = StockLocationRepository(session)
        self.bal_repo = StockBalanceRepository(session)
        self.mov_repo = StockMovementRepository(session)
        self.hall_repo = HallRepository(session)
        self.prod_repo = ProductRepository(session)

    async def receive(self, req: StockReceiveRequest) -> StockBalance:
        """Загрузить товар в зал (приход)."""
        hall = await self.hall_repo.get(req.hall_id)
        if hall is None:
            raise HTTPException(status_code=404, detail=f"Hall {req.hall_id} not found")

        product = await self.prod_repo.get(req.product_id)
        if product is None:
            raise HTTPException(
                status_code=404, detail=f"Product {req.product_id} not found"
            )

        loc = await self.loc_repo.get_or_create(req.hall_id, req.product_id)
        bal = await self.bal_repo.get_or_create(loc.id)

        bal.quantity += req.quantity

        await self.mov_repo.log(
            product_id=req.product_id,
            hall_id=req.hall_id,
            quantity=req.quantity,
            movement_type=MovementType.receive,
            note=req.note,
        )
        return bal

    async def get_balance(self, hall_id: int, product_id: int) -> StockBalance:
        loc = await self.loc_repo.get_by_hall_and_product(hall_id, product_id)
        if loc is None or loc.balance is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No stock for product {product_id} in hall {hall_id}",
            )
        return loc.balance

    async def get_hall_inventory(self, hall_id: int) -> list[HallInventoryItem]:
        # Все активные товары
        all_products = await self.prod_repo.get_active()

        # Остатки по залу: {product_id: StockLocation}
        locations = await self.loc_repo.get_hall_inventory(hall_id)
        loc_map = {loc.product_id: loc for loc in locations}

        # Последние приходы: {product_id: datetime}
        last_received = await self.mov_repo.get_last_receive_per_product(hall_id)

        result = []
        for prod in all_products:
            loc = loc_map.get(prod.id)
            bal = loc.balance if loc else None
            qty = bal.quantity if bal else 0
            res = bal.reserved_quantity if bal else 0
            result.append(
                HallInventoryItem(
                    product_id=prod.id,
                    product_name=prod.name,
                    sku=prod.sku,
                    unit=prod.unit,
                    quantity=qty,
                    reserved_quantity=res,
                    available=qty - res,
                    last_received_at=last_received.get(prod.id),
                )
            )
        return result

    # ──────────────────────────────────────────────────────────
    # Внутренние методы, используемые OrderService
    # ──────────────────────────────────────────────────────────

    async def reserve(
        self,
        hall_id: int,
        product_id: int,
        quantity: int,
        order_id: int,
    ) -> None:
        """Зарезервировать товар при добавлении позиции в заказ."""
        loc = await self.loc_repo.get_by_hall_and_product(hall_id, product_id)
        if loc is None or loc.balance is None:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Product {product_id} is not available in hall {hall_id}",
            )
        bal = loc.balance
        if bal.available < quantity:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=(
                    f"Insufficient stock for product {product_id}: "
                    f"available={bal.available}, requested={quantity}"
                ),
            )
        bal.reserved_quantity += quantity
        await self.mov_repo.log(
            product_id=product_id,
            hall_id=hall_id,
            quantity=-quantity,
            movement_type=MovementType.reserve,
            reference_type="order",
            reference_id=order_id,
        )

    async def write_off(
        self,
        hall_id: int,
        product_id: int,
        quantity: int,
        order_id: int,
    ) -> None:
        """Списать товар при выполнении заказа."""
        loc = await self.loc_repo.get_by_hall_and_product(hall_id, product_id)
        if loc is None or loc.balance is None:
            raise HTTPException(status_code=404, detail="Stock location not found")
        bal = loc.balance
        bal.quantity -= quantity
        bal.reserved_quantity -= quantity
        await self.mov_repo.log(
            product_id=product_id,
            hall_id=hall_id,
            quantity=-quantity,
            movement_type=MovementType.write_off,
            reference_type="order",
            reference_id=order_id,
        )

    async def cancel_reserve(
        self,
        hall_id: int,
        product_id: int,
        quantity: int,
        order_id: int,
    ) -> None:
        """Снять резерв при отмене заказа."""
        loc = await self.loc_repo.get_by_hall_and_product(hall_id, product_id)
        if loc is None or loc.balance is None:
            return  # уже нет — просто пропускаем
        bal = loc.balance
        bal.reserved_quantity = max(0, bal.reserved_quantity - quantity)
        await self.mov_repo.log(
            product_id=product_id,
            hall_id=hall_id,
            quantity=quantity,
            movement_type=MovementType.cancel_reserve,
            reference_type="order",
            reference_id=order_id,
        )
