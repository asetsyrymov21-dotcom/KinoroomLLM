from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_session
from app.schemas.product import ProductCreate, ProductRead, ProductUpdate
from app.services.product import ProductService

router = APIRouter(prefix="/products", tags=["Products"])


@router.post("/", response_model=ProductRead, status_code=201)
async def create_product(
    data: ProductCreate,
    session: AsyncSession = Depends(get_session),
):
    """Добавить новый товар."""
    svc = ProductService(session)
    return await svc.create(data)


@router.get("/", response_model=list[ProductRead])
async def list_products(
    active_only: bool = True,
    session: AsyncSession = Depends(get_session),
):
    svc = ProductService(session)
    return await svc.list_active() if active_only else await svc.list_all()


@router.get("/{product_id}", response_model=ProductRead)
async def get_product(
    product_id: int,
    session: AsyncSession = Depends(get_session),
):
    svc = ProductService(session)
    return await svc.get_or_404(product_id)


@router.patch("/{product_id}", response_model=ProductRead)
async def update_product(
    product_id: int,
    data: ProductUpdate,
    session: AsyncSession = Depends(get_session),
):
    svc = ProductService(session)
    return await svc.update(product_id, data)


@router.delete("/{product_id}", status_code=204)
async def delete_product(
    product_id: int,
    session: AsyncSession = Depends(get_session),
):
    """Удалить товар."""
    svc = ProductService(session)
    await svc.delete(product_id)
