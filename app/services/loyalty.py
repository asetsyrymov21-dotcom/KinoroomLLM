"""
Сервис системы лояльности.

Логика:
  - Считаем завершённые визиты пользователя в рамках тенанта.
  - Если текущий визит (по счёту) совпадает с visits_required активного правила —
    применяем награду при создании брони.
  - Пример: правило visits_required=5, reward_type=discount, reward_value=20
    → каждый 5-й, 10-й, 15-й... визит = скидка 20%.
  - Пример: правило visits_required=5, reward_type=free_booking
    → каждый 5-й визит = аренда зала бесплатно.
"""
from decimal import Decimal

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.loyalty import LoyaltyRule, RewardType
from app.repositories.loyalty import LoyaltyRepository
from app.schemas.loyalty import (
    LoyaltyRuleCreate,
    LoyaltyRuleUpdate,
    UserLoyaltyStatus,
)


class LoyaltyService:
    def __init__(self, session: AsyncSession) -> None:
        self.repo = LoyaltyRepository(session)

    # ── CRUD правил ────────────────────────────────────────────────

    async def create_rule(self, data: LoyaltyRuleCreate) -> LoyaltyRule:
        return await self.repo.create(**data.model_dump())

    async def get_rule_or_404(self, rule_id: int) -> LoyaltyRule:
        rule = await self.repo.get(rule_id)
        if rule is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Loyalty rule {rule_id} not found",
            )
        return rule

    async def list_rules(self, active_only: bool = False) -> list[LoyaltyRule]:
        return await self.repo.list_active() if active_only else await self.repo.list_all()

    async def update_rule(self, rule_id: int, data: LoyaltyRuleUpdate) -> LoyaltyRule:
        rule = await self.get_rule_or_404(rule_id)
        for field, value in data.model_dump(exclude_none=True).items():
            setattr(rule, field, value)
        return rule

    async def delete_rule(self, rule_id: int) -> None:
        rule = await self.get_rule_or_404(rule_id)
        await self.repo.delete(rule)

    # ── Статус пользователя ────────────────────────────────────────

    async def get_user_status(self, user_id: int, tenant_id: int) -> UserLoyaltyStatus:
        completed = await self.repo.count_completed_visits(user_id, tenant_id)
        # Следующий визит = completed + 1
        next_visit = completed + 1
        rules = await self.repo.list_active()

        active_reward = self._find_rule_for_visit(rules, next_visit)
        next_rule, visits_until = self._find_next_rule(rules, completed)

        return UserLoyaltyStatus(
            user_id=user_id,
            completed_visits=completed,
            next_rule=next_rule,
            visits_until_reward=visits_until,
            active_reward=active_reward,
        )

    # ── Применение к брони ─────────────────────────────────────────

    async def apply_to_booking(
        self, user_id: int, base_price: Decimal, tenant_id: int
    ) -> tuple[Decimal, Decimal | None, LoyaltyRule | None]:
        """
        Возвращает (итоговая_цена, discount_pct, применённое_правило).
        Если правило free_booking — цена = 0, discount_pct = 100.
        Если правило discount — цена уменьшается на reward_value %.
        Визиты считаются только внутри тенанта.
        """
        completed = await self.repo.count_completed_visits(user_id, tenant_id)
        next_visit = completed + 1
        rules = await self.repo.list_active()
        rule = self._find_rule_for_visit(rules, next_visit)

        if rule is None:
            return base_price, None, None

        if rule.reward_type == RewardType.free_booking:
            return Decimal("0"), Decimal("100"), rule

        pct = rule.reward_value
        discounted = base_price * (1 - pct / 100)
        discounted = discounted.quantize(Decimal("0.01"))
        return discounted, pct, rule

    # ── helpers ────────────────────────────────────────────────────

    @staticmethod
    def _find_rule_for_visit(
        rules: list[LoyaltyRule], visit_number: int
    ) -> LoyaltyRule | None:
        """Правило срабатывает если visit_number кратно visits_required."""
        for rule in sorted(rules, key=lambda r: r.visits_required, reverse=True):
            if visit_number % rule.visits_required == 0:
                return rule
        return None

    @staticmethod
    def _find_next_rule(
        rules: list[LoyaltyRule], completed: int
    ) -> tuple[LoyaltyRule | None, int | None]:
        """Ближайшее незаработанное правило и сколько визитов до него."""
        if not rules:
            return None, None
        next_visit = completed + 1
        best_rule = None
        best_distance = None
        for rule in rules:
            n = rule.visits_required
            # Следующее кратное >= next_visit
            remainder = next_visit % n
            distance = (n - remainder) % n or n
            next_trigger = next_visit + distance - 1  # уже на этом визите?
            # Сколько визитов до следующего срабатывания
            visits_left = next_trigger - next_visit + 1
            if visits_left <= 0:
                visits_left = n
            if best_distance is None or visits_left < best_distance:
                best_distance = visits_left
                best_rule = rule
        return best_rule, best_distance
