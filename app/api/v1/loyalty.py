from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_session
from app.models.staff import Staff
from app.schemas.loyalty import (
    LoyaltyRuleCreate,
    LoyaltyRuleRead,
    LoyaltyRuleUpdate,
    UserLoyaltyStatus,
)
from app.services.auth import get_current_staff
from app.services.loyalty import LoyaltyService

router = APIRouter(prefix="/loyalty", tags=["Loyalty"])


@router.post("/rules", response_model=LoyaltyRuleRead, status_code=201)
async def create_rule(
    data: LoyaltyRuleCreate,
    session: AsyncSession = Depends(get_session),
    _: Staff = Depends(get_current_staff),
):
    return await LoyaltyService(session).create_rule(data)


@router.get("/rules", response_model=list[LoyaltyRuleRead])
async def list_rules(
    active_only: bool = False,
    session: AsyncSession = Depends(get_session),
):
    return await LoyaltyService(session).list_rules(active_only=active_only)


@router.patch("/rules/{rule_id}", response_model=LoyaltyRuleRead)
async def update_rule(
    rule_id: int,
    data: LoyaltyRuleUpdate,
    session: AsyncSession = Depends(get_session),
    _: Staff = Depends(get_current_staff),
):
    return await LoyaltyService(session).update_rule(rule_id, data)


@router.delete("/rules/{rule_id}", status_code=204)
async def delete_rule(
    rule_id: int,
    session: AsyncSession = Depends(get_session),
    _: Staff = Depends(get_current_staff),
):
    await LoyaltyService(session).delete_rule(rule_id)


@router.get("/users/{user_id}", response_model=UserLoyaltyStatus)
async def get_user_loyalty(
    user_id: int,
    tenant_id: int = Query(1, description="ID тенанта"),
    session: AsyncSession = Depends(get_session),
):
    """Статус лояльности пользователя: визиты, ближайшая награда, текущая награда."""
    return await LoyaltyService(session).get_user_status(user_id, tenant_id)
