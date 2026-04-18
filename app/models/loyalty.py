import enum
from decimal import Decimal

from sqlalchemy import Boolean, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class RewardType(str, enum.Enum):
    discount = "discount"          # скидка reward_value %
    free_booking = "free_booking"  # бесплатная аренда зала


class LoyaltyRule(Base):
    __tablename__ = "loyalty_rules"

    id: Mapped[int] = mapped_column(primary_key=True)
    visits_required: Mapped[int] = mapped_column(nullable=False)
    reward_type: Mapped[RewardType] = mapped_column(String(30), nullable=False)
    reward_value: Mapped[Decimal] = mapped_column(
        Numeric(5, 2), nullable=False, default=Decimal("0")
    )
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    def __repr__(self) -> str:
        return (
            f"<LoyaltyRule id={self.id} visits={self.visits_required} "
            f"reward={self.reward_type} value={self.reward_value}>"
        )
