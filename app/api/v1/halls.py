from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_session
from app.schemas.hall import HallCreate, HallRead, HallUpdate
from app.services.hall import HallService

router = APIRouter(prefix="/halls", tags=["Halls"])


@router.post("/", response_model=HallRead, status_code=201)
async def create_hall(
    data: HallCreate,
    session: AsyncSession = Depends(get_session),
):
    """Создать новый зал."""
    svc = HallService(session)
    return await svc.create(data)


@router.get("/", response_model=list[HallRead])
async def list_halls(
    active_only: bool = False,
    session: AsyncSession = Depends(get_session),
):
    """Список всех залов (или только активных)."""
    svc = HallService(session)
    return await svc.list_active() if active_only else await svc.list_all()


@router.get("/{hall_id}", response_model=HallRead)
async def get_hall(
    hall_id: int,
    session: AsyncSession = Depends(get_session),
):
    svc = HallService(session)
    return await svc.get_or_404(hall_id)


@router.patch("/{hall_id}", response_model=HallRead)
async def update_hall(
    hall_id: int,
    data: HallUpdate,
    session: AsyncSession = Depends(get_session),
):
    svc = HallService(session)
    return await svc.update(hall_id, data)


@router.delete("/{hall_id}", status_code=204)
async def delete_hall(
    hall_id: int,
    session: AsyncSession = Depends(get_session),
):
    """Удалить зал."""
    svc = HallService(session)
    await svc.delete(hall_id)
