from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.models.booking import BookingStatus


class BookingCreate(BaseModel):
    user_id: int
    hall_id: int
    start_time: datetime
    end_time: datetime
    is_open_ended: bool = False

    @model_validator(mode="after")
    def check_times(self) -> "BookingCreate":
        if self.end_time <= self.start_time:
            raise ValueError("end_time must be after start_time")
        return self


class BookingUserInfo(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    name: str
    phone: str | None = None


class BookingRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    hall_id: int
    start_time: datetime
    end_time: datetime
    status: BookingStatus
    total_price: Decimal | None
    discount_pct: Decimal | None = None
    extra_charge: Decimal | None = None
    created_at: datetime
    completed_at: datetime | None = None
    is_open_ended: bool = False
    user: BookingUserInfo | None = None


class BookingStatusUpdate(BaseModel):
    status: BookingStatus = Field(
        ..., description="Новый статус: active | completed | cancelled"
    )


class ExtraChargeRequest(BaseModel):
    amount: Decimal = Field(..., gt=0, description="Сумма доплаты в тенге")


# ── История сеансов ──────────────────────────────────────────

class SessionHistoryItem(BaseModel):
    """Одна позиция (товар) в заказе сеанса."""
    product_name: str
    quantity: int
    price_at_order: Decimal
    subtotal: Decimal


class SessionHistoryOrder(BaseModel):
    """Заказ внутри сеанса."""
    id: int
    status: str
    created_at: datetime
    items: list[SessionHistoryItem] = []
    order_total: Decimal = Decimal("0")


class SessionHistoryRead(BaseModel):
    """Полная запись завершённого сеанса."""
    booking_id: int
    hall_name: str
    start_time: datetime
    end_time: datetime          # плановое окончание
    completed_at: datetime | None   # фактическое
    duration_minutes: int       # фактическая длительность в минутах
    hall_cost: Decimal          # стоимость зала
    extra_charge: Decimal       # доплаты (доп. люди и т.п.)
    orders: list[SessionHistoryOrder] = []
    food_total: Decimal         # итого по товарам/заказам
    grand_total: Decimal        # зал + доплаты + еда
