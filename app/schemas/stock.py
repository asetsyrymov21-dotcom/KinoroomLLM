from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.stock import MovementType


class StockReceiveRequest(BaseModel):
    """Загрузить товар в зал."""
    hall_id: int
    product_id: int
    quantity: int = Field(..., gt=0)
    note: str | None = None


class StockBalanceRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    stock_location_id: int
    quantity: int
    reserved_quantity: int
    available: int  # computed property


class StockLocationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    hall_id: int
    product_id: int
    balance: StockBalanceRead | None = None


class HallInventoryItem(BaseModel):
    """Позиция инвентаря зала для отображения."""
    product_id: int
    product_name: str
    sku: str | None
    unit: str
    quantity: int
    reserved_quantity: int
    available: int
    last_received_at: datetime | None = None  # последний приход товара


class StockMovementRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    product_id: int
    hall_id: int
    quantity: int
    movement_type: MovementType
    reference_type: str | None
    reference_id: int | None
    note: str | None
    created_at: datetime
