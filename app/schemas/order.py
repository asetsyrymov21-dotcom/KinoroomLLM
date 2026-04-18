from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from app.models.order import OrderStatus


class OrderCreate(BaseModel):
    booking_id: int


class OrderItemAdd(BaseModel):
    product_id: int
    quantity: int = Field(..., gt=0)


class OrderItemRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    order_id: int
    product_id: int
    quantity: int
    price_at_order: Decimal


class OrderRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    booking_id: int
    status: OrderStatus
    created_at: datetime
    completed_at: datetime | None
    items: list[OrderItemRead] = []
