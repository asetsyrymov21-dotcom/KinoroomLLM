import enum
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class MovementType(str, enum.Enum):
    receive = "receive"           # приход товара в зал
    reserve = "reserve"           # резерв при создании заказа
    write_off = "write_off"       # списание при выполнении заказа
    cancel_reserve = "cancel_reserve"  # снятие резерва при отмене заказа


class StockLocation(Base):
    """Связь: какой товар есть в каком зале."""

    __tablename__ = "stock_locations"
    __table_args__ = (UniqueConstraint("hall_id", "product_id"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    hall_id: Mapped[int] = mapped_column(ForeignKey("halls.id"), nullable=False)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"), nullable=False)

    hall: Mapped["Hall"] = relationship(back_populates="stock_locations")
    product: Mapped["Product"] = relationship(back_populates="stock_locations")
    balance: Mapped["StockBalance"] = relationship(
        back_populates="location", uselist=False, cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<StockLocation hall={self.hall_id} product={self.product_id}>"


class StockBalance(Base):
    """Текущий остаток по локации: qty — физически, reserved — зарезервировано."""

    __tablename__ = "stock_balances"

    id: Mapped[int] = mapped_column(primary_key=True)
    stock_location_id: Mapped[int] = mapped_column(
        ForeignKey("stock_locations.id"), nullable=False, unique=True
    )
    quantity: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    reserved_quantity: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    location: Mapped["StockLocation"] = relationship(back_populates="balance")

    @property
    def available(self) -> int:
        return self.quantity - self.reserved_quantity

    def __repr__(self) -> str:
        return (
            f"<StockBalance loc={self.stock_location_id} "
            f"qty={self.quantity} reserved={self.reserved_quantity}>"
        )


class StockMovement(Base):
    """Лог всех движений товара."""

    __tablename__ = "stock_movements"

    id: Mapped[int] = mapped_column(primary_key=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id", ondelete="CASCADE"), nullable=False)
    hall_id: Mapped[int] = mapped_column(ForeignKey("halls.id", ondelete="CASCADE"), nullable=False)
    # положительное — приход, отрицательное — расход
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    movement_type: Mapped[MovementType] = mapped_column(String(20), nullable=False)
    # ссылка на объект-источник (order_id, booking_id и т.д.)
    reference_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    reference_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    def __repr__(self) -> str:
        return (
            f"<StockMovement {self.movement_type} "
            f"product={self.product_id} qty={self.quantity:+d}>"
        )
