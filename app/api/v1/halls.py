from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_session
from app.models.staff import Staff
from app.schemas.hall import HallCreate, HallRead, HallUpdate
from app.services.auth import get_current_staff
from app.services.hall import HallService

router = APIRouter(prefix="/halls", tags=["Halls"])


@router.post("/", response_model=HallRead, status_code=201)
async def create_hall(
    data: HallCreate,
    session: AsyncSession = Depends(get_session),
    current: Staff = Depends(get_current_staff),
):
    """Создать новый зал."""
    svc = HallService(session, current.tenant_id)
    return await svc.create(data)


@router.get("/", response_model=list[HallRead])
async def list_halls(
    active_only: bool = False,
    tenant_id: int = Query(1, description="ID тенанта (передаётся мини-аппом)"),
    session: AsyncSession = Depends(get_session),
):
    """Список залов. Для оператора tenant_id берётся из JWT через auth-зависимость
    на уровне фронта; для мини-аппа передаётся query-параметром (default=1)."""
    svc = HallService(session, tenant_id)
    return await svc.list_active() if active_only else await svc.list_all()


@router.get("/{hall_id}", response_model=HallRead)
async def get_hall(
    hall_id: int,
    tenant_id: int = Query(1, description="ID тенанта"),
    session: AsyncSession = Depends(get_session),
):
    svc = HallService(session, tenant_id)
    return await svc.get_or_404(hall_id)


@router.patch("/{hall_id}", response_model=HallRead)
async def update_hall(
    hall_id: int,
    data: HallUpdate,
    session: AsyncSession = Depends(get_session),
    current: Staff = Depends(get_current_staff),
):
    svc = HallService(session, current.tenant_id)
    return await svc.update(hall_id, data)


@router.delete("/{hall_id}", status_code=204)
async def delete_hall(
    hall_id: int,
    session: AsyncSession = Depends(get_session),
    current: Staff = Depends(get_current_staff),
):
    """Удалить зал."""
    svc = HallService(session, current.tenant_id)
    await svc.delete(hall_id)
