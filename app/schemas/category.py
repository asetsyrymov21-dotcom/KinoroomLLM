from pydantic import BaseModel, ConfigDict, Field


class CategoryCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    emoji: str | None = Field(None, max_length=10)
    position: int = 0
    is_active: bool = True
    parent_id: int | None = None


class CategoryUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=100)
    emoji: str | None = None
    position: int | None = None
    is_active: bool | None = None
    parent_id: int | None = None


class CategoryRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    emoji: str | None
    position: int
    is_active: bool
    parent_id: int | None
