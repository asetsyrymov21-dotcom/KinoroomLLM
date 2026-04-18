from decimal import Decimal

from sqlalchemy import Boolean, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Hall(Base):
    __tablename__ = "halls"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    capacity: Mapped[int] = mapped_column(nullable=False, default=1)
    price_per_hour: Mapped[Decimal] = mapped_column(
        Numeric(10, 2), nullable=False, default=0
    )
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    bookings: Mapped[list["Booking"]] = relationship(
        back_populates="hall", cascade="all, delete-orphan"
    )
    stock_locations: Mapped[list["StockLocation"]] = relationship(
        back_populates="hall", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Hall id={self.id} name={self.name!r}>"
