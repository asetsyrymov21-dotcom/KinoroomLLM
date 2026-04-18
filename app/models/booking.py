import enum
from datetime import datetime
from decimal import Decimal

from sqlalchemy import Boolean, DateTime, ForeignKey, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class BookingStatus(str, enum.Enum):
    pending = "pending"
    active = "active"
    completed = "completed"
    cancelled = "cancelled"


class Booking(Base):
    __tablename__ = "bookings"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    hall_id: Mapped[int] = mapped_column(ForeignKey("halls.id"), nullable=False)
    start_time: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    end_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    status: Mapped[BookingStatus] = mapped_column(
        String(20), nullable=False, default=BookingStatus.pending
    )
    total_price: Mapped[Decimal | None] = mapped_column(
        Numeric(10, 2), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    is_open_ended: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default="false"
    )
    discount_pct: Mapped[Decimal | None] = mapped_column(
        Numeric(5, 2), nullable=True
    )
    extra_charge: Mapped[Decimal | None] = mapped_column(
        Numeric(10, 2), nullable=True
    )

    user: Mapped["User"] = relationship(back_populates="bookings")
    hall: Mapped["Hall"] = relationship(back_populates="bookings")
    orders: Mapped[list["Order"]] = relationship(
        back_populates="booking", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return (
            f"<Booking id={self.id} hall_id={self.hall_id} "
            f"status={self.status} {self.start_time}–{self.end_time}>"
        )
