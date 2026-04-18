"""
FLOW 2: Заказ товаров во время активной брони
FLOW 3: Резерв / списание

  создать заказ (требует active booking)
    → добавить позицию → резерв товара
    → complete → списание
    → cancel   → снятие резерва
"""
from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.booking import BookingStatus
from app.models.order import Order, OrderItem, OrderStatus
from app.repositories.booking import BookingRepository
from app.repositories.order import OrderItemRepository, OrderRepository
from app.repositories.product import ProductRepository
from app.repositories.stock import StockLocationRepository
from app.schemas.order import OrderCreate, OrderItemAdd
from app.services.stock import StockService


class OrderService:
    def __init__(self, session: AsyncSession) -> None:
        self.repo = OrderRepository(session)
        self.item_repo = OrderItemRepository(session)
        self.booking_repo = BookingRepository(session)
        self.product_repo = ProductRepository(session)
        self.stock_svc = StockService(session)
        self.loc_repo = StockLocationRepository(session)

    # ──────────────────────────── создание заказа ──────────────────────────────

    async def create(self, data: OrderCreate) -> Order:
        """Создать новый заказ. Бронь должна быть active."""
        booking = await self.booking_repo.get(data.booking_id)
        if booking is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Booking {data.booking_id} not found",
            )
        if booking.status not in (BookingStatus.active, BookingStatus.pending):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    f"Cannot create order for booking with status '{booking.status}'. "
                    "Booking must be active or pending."
                ),
            )
        order = await self.repo.create(
            booking_id=data.booking_id,
            status=OrderStatus.pending,
        )
        # Перезагружаем с items чтобы избежать lazy load в async контексте
        return await self.repo.get_with_items(order.id)

    # ──────────────────────────── добавить позицию ─────────────────────────────

    async def add_item(self, order_id: int, data: OrderItemAdd) -> OrderItem:
        """
        Добавить товар в заказ + зарезервировать остаток.
        Заказ должен быть pending.
        """
        order = await self.repo.get_with_items(order_id)
        if order is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Order {order_id} not found",
            )
        if order.status != OrderStatus.pending:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot add items to order with status '{order.status}'",
            )

        product = await self.product_repo.get(data.product_id)
        if product is None or not product.is_active:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Product {data.product_id} not found or inactive",
            )

        # Достать hall_id из брони
        booking = await self.booking_repo.get(order.booking_id)

        # Резерв на складе — только если товар заведён в этом зале
        loc = await self.loc_repo.get_by_hall_and_product(booking.hall_id, data.product_id)
        if loc is not None and loc.balance is not None:
            await self.stock_svc.reserve(
                hall_id=booking.hall_id,
                product_id=data.product_id,
                quantity=data.quantity,
                order_id=order_id,
            )

        item = await self.item_repo.create(
            order_id=order_id,
            product_id=data.product_id,
            quantity=data.quantity,
            price_at_order=product.price,
        )
        return item

    # ──────────────────────────── выполнить заказ ──────────────────────────────

    async def complete(self, order_id: int) -> Order:
        """
        Оператор нажал «Выполнено»:
        - списать товар со склада (quantity - reserved)
        - перевести заказ в completed
        """
        order = await self.repo.get_with_items(order_id)
        if order is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Order {order_id} not found",
            )
        if order.status != OrderStatus.pending:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot complete order with status '{order.status}'",
            )

        booking = await self.booking_repo.get(order.booking_id)

        for item in order.items:
            loc = await self.loc_repo.get_by_hall_and_product(booking.hall_id, item.product_id)
            if loc is not None and loc.balance is not None:
                await self.stock_svc.write_off(
                    hall_id=booking.hall_id,
                    product_id=item.product_id,
                    quantity=item.quantity,
                    order_id=order_id,
                )

        order.status = OrderStatus.completed
        order.completed_at = datetime.now(timezone.utc)
        return order

    # ──────────────────────────── отменить заказ ───────────────────────────────

    async def cancel(self, order_id: int) -> Order:
        """Отменить заказ — снять резервы."""
        order = await self.repo.get_with_items(order_id)
        if order is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Order {order_id} not found",
            )
        if order.status != OrderStatus.pending:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot cancel order with status '{order.status}'",
            )

        booking = await self.booking_repo.get(order.booking_id)

        for item in order.items:
            loc = await self.loc_repo.get_by_hall_and_product(booking.hall_id, item.product_id)
            if loc is not None and loc.balance is not None:
                await self.stock_svc.cancel_reserve(
                    hall_id=booking.hall_id,
                    product_id=item.product_id,
                    quantity=item.quantity,
                    order_id=order_id,
                )

        order.status = OrderStatus.cancelled
        return order

    # ──────────────────────────── чтение ───────────────────────────────────────

    async def get_or_404(self, order_id: int) -> Order:
        order = await self.repo.get_with_items(order_id)
        if order is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Order {order_id} not found",
            )
        return order

    async def list_by_booking(self, booking_id: int) -> list[Order]:
        return await self.repo.get_all_by_booking(booking_id)

    async def list_pending(self, booking_id: int) -> list[Order]:
        """Все висящие заказы по брони — для экрана оператора."""
        return await self.repo.get_pending_by_booking(booking_id)
