from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_session
from app.schemas.category import CategoryCreate, CategoryRead, CategoryUpdate
from app.services.category import CategoryService

router = APIRouter(prefix="/categories", tags=["Categories"])


@router.post("/", response_model=CategoryRead, status_code=201)
async def create_category(
    data: CategoryCreate,
    session: AsyncSession = Depends(get_session),
):
    return await CategoryService(session).create(data)


@router.get("/", response_model=list[CategoryRead])
async def list_categories(
    active_only: bool = False,
    session: AsyncSession = Depends(get_session),
):
    svc = CategoryService(session)
    return await svc.list_active() if active_only else await svc.list_all()


@router.get("/{category_id}", response_model=CategoryRead)
async def get_category(
    category_id: int,
    session: AsyncSession = Depends(get_session),
):
    return await CategoryService(session).get_or_404(category_id)


@router.patch("/{category_id}", response_model=CategoryRead)
async def update_category(
    category_id: int,
    data: CategoryUpdate,
    session: AsyncSession = Depends(get_session),
):
    return await CategoryService(session).update(category_id, data)


@router.delete("/{category_id}", status_code=204)
async def delete_category(
    category_id: int,
    session: AsyncSession = Depends(get_session),
):
    await CategoryService(session).delete(category_id)
