from datetime import datetime

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.stock import MovementType, StockBalance, StockLocation, StockMovement
from app.repositories.base import BaseRepository


class StockLocationRepository(BaseRepository[StockLocation]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(StockLocation, session)

    async def get_by_hall_and_product(
        self, hall_id: int, product_id: int
    ) -> StockLocation | None:
        result = await self.session.execute(
            select(StockLocation)
            .options(selectinload(StockLocation.balance))
            .where(
                StockLocation.hall_id == hall_id,
                StockLocation.product_id == product_id,
            )
        )
        return result.scalar_one_or_none()

    async def get_hall_inventory(self, hall_id: int) -> list[StockLocation]:
        result = await self.session.execute(
            select(StockLocation)
            .options(
                selectinload(StockLocation.balance),
                selectinload(StockLocation.product),
            )
            .where(StockLocation.hall_id == hall_id)
        )
        return list(result.scalars().all())

    async def get_or_create(self, hall_id: int, product_id: int) -> StockLocation:
        loc = await self.get_by_hall_and_product(hall_id, product_id)
        if loc is None:
            loc = await self.create(hall_id=hall_id, product_id=product_id)
        return loc


class StockBalanceRepository(BaseRepository[StockBalance]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(StockBalance, session)

    async def get_by_location(self, stock_location_id: int) -> StockBalance | None:
        result = await self.session.execute(
            select(StockBalance).where(
                StockBalance.stock_location_id == stock_location_id
            )
        )
        return result.scalar_one_or_none()

    async def get_or_create(self, stock_location_id: int) -> StockBalance:
        bal = await self.get_by_location(stock_location_id)
        if bal is None:
            bal = await self.create(
                stock_location_id=stock_location_id,
                quantity=0,
                reserved_quantity=0,
            )
        return bal


class StockMovementRepository(BaseRepository[StockMovement]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(StockMovement, session)

    async def log(
        self,
        *,
        product_id: int,
        hall_id: int,
        quantity: int,
        movement_type: MovementType,
        reference_type: str | None = None,
        reference_id: int | None = None,
        note: str | None = None,
    ) -> StockMovement:
        return await self.create(
            product_id=product_id,
            hall_id=hall_id,
            quantity=quantity,
            movement_type=movement_type,
            reference_type=reference_type,
            reference_id=reference_id,
            note=note,
        )

    async def get_by_hall(self, hall_id: int) -> list[StockMovement]:
        result = await self.session.execute(
            select(StockMovement)
            .where(StockMovement.hall_id == hall_id)
            .order_by(StockMovement.created_at.desc())
        )
        return list(result.scalars().all())

    async def get_last_receive_per_product(
        self, hall_id: int
    ) -> dict[int, datetime]:
        """
        Возвращает словарь {product_id: последняя дата прихода}
        для указанного зала.
        """
        result = await self.session.execute(
            select(
                StockMovement.product_id,
                func.max(StockMovement.created_at).label("last_at"),
            )
            .where(
                StockMovement.hall_id == hall_id,
                StockMovement.movement_type == MovementType.receive,
            )
            .group_by(StockMovement.product_id)
        )
        return {row.product_id: row.last_at for row in result.all()}
