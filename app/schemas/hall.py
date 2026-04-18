from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class HallCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = None
    capacity: int = Field(1, ge=1)
    price_per_hour: Decimal = Field(Decimal("0"), ge=0)
    is_active: bool = True


class HallUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=255)
    description: str | None = None
    capacity: int | None = Field(None, ge=1)
    price_per_hour: Decimal | None = Field(None, ge=0)
    is_active: bool | None = None


class HallRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    description: str | None
    capacity: int
    price_per_hour: Decimal
    is_active: bool
