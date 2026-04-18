from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class ProductCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    sku: str | None = Field(None, max_length=100)
    description: str | None = None
    price: Decimal = Field(Decimal("0"), ge=0)
    cost_price: Decimal | None = Field(None, ge=0)
    unit: str = Field("шт", max_length=20)
    is_active: bool = True
    category_id: int | None = None


class ProductUpdate(BaseModel):
    name: str | None = Field(None, min_length=1)
    sku: str | None = None
    description: str | None = None
    price: Decimal | None = Field(None, ge=0)
    cost_price: Decimal | None = Field(None, ge=0)
    unit: str | None = None
    is_active: bool | None = None
    category_id: int | None = None


class ProductRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    sku: str | None
    description: str | None
    price: Decimal
    cost_price: Decimal | None
    unit: str
    is_active: bool
    category_id: int | None
