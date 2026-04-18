from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class UserCreate(BaseModel):
    telegram_id: int
    name: str = Field(..., min_length=1, max_length=255)
    phone: str | None = Field(None, max_length=20)


class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    telegram_id: int
    name: str
    phone: str | None
    created_at: datetime
