from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from app.models.loyalty import RewardType


class LoyaltyRuleCreate(BaseModel):
    visits_required: int = Field(..., ge=1)
    reward_type: RewardType
    reward_value: Decimal = Field(Decimal("0"), ge=0)
    description: str | None = None
    is_active: bool = True


class LoyaltyRuleUpdate(BaseModel):
    visits_required: int | None = Field(None, ge=1)
    reward_type: RewardType | None = None
    reward_value: Decimal | None = Field(None, ge=0)
    description: str | None = None
    is_active: bool | None = None


class LoyaltyRuleRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    visits_required: int
    reward_type: RewardType
    reward_value: Decimal
    description: str | None
    is_active: bool


class UserLoyaltyStatus(BaseModel):
    """Статус лояльности пользователя."""
    user_id: int
    completed_visits: int
    next_rule: LoyaltyRuleRead | None     # ближайшее правило
    visits_until_reward: int | None       # сколько визитов осталось
    active_reward: LoyaltyRuleRead | None # награда применяется к ЭТОМУ бронированию
