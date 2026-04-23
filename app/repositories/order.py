from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.order import Order, OrderItem, OrderStatus
from app.repositories.base import TenantScopedRepository


class OrderRepository(TenantScopedRepository[Order]):
    def __init__(self, session: AsyncSession, tenant_id: int) -> None:
        super().__init__(Order, session, tenant_id)

    async def get_with_items(self, id: int) -> Order | None:
        result = await self.session.execute(
            select(Order)
            .options(selectinload(Order.items))
            .where(
                Order.id == id,
                Order.tenant_id == self.tenant_id,
            )
        )
        return result.scalar_one_or_none()

    async def get_pending_by_booking(self, booking_id: int) -> list[Order]:
        result = await self.session.execute(
            select(Order)
            .options(selectinload(Order.items))
            .where(
                Order.tenant_id == self.tenant_id,
                Order.booking_id == booking_id,
                Order.status == OrderStatus.pending,
            )
            .order_by(Order.created_at.asc())
        )
        return list(result.scalars().all())

    async def get_all_by_booking(self, booking_id: int) -> list[Order]:
        result = await self.session.execute(
            select(Order)
            .options(selectinload(Order.items))
            .where(
                Order.tenant_id == self.tenant_id,
                Order.booking_id == booking_id,
            )
            .order_by(Order.created_at.desc())
        )
        return list(result.scalars().all())


class OrderItemRepository(TenantScopedRepository[OrderItem]):
    def __init__(self, session: AsyncSession, tenant_id: int) -> None:
        super().__init__(OrderItem, session, tenant_id)
