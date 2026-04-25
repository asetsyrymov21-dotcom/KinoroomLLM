from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_session
from app.models.staff import Staff
from app.schemas.product import ProductCreate, ProductRead, ProductUpdate
from app.services.auth import get_current_staff
from app.services.product import ProductService

router = APIRouter(prefix="/products", tags=["Products"])


@router.post("", response_model=ProductRead, status_code=201)
async def create_product(
    data: ProductCreate,
    session: AsyncSession = Depends(get_session),
    current: Staff = Depends(get_current_staff),
):
    """Добавить новый товар."""
    svc = ProductService(session, current.tenant_id)
    return await svc.create(data)


@router.get("", response_model=list[ProductRead])
async def list_products(
    active_only: bool = True,
    tenant_id: int = Query(1, description="ID тенанта"),
    session: AsyncSession = Depends(get_session),
):
    svc = ProductService(session, tenant_id)
    return await svc.list_active() if active_only else await svc.list_all()


@router.get("/{product_id}", response_model=ProductRead)
async def get_product(
    product_id: int,
    tenant_id: int = Query(1, description="ID тенанта"),
    session: AsyncSession = Depends(get_session),
):
    svc = ProductService(session, tenant_id)
    return await svc.get_or_404(product_id)


@router.patch("/{product_id}", response_model=ProductRead)
async def update_product(
    product_id: int,
    data: ProductUpdate,
    session: AsyncSession = Depends(get_session),
    current: Staff = Depends(get_current_staff),
):
    svc = ProductService(session, current.tenant_id)
    return await svc.update(product_id, data)


@router.delete("/{product_id}", status_code=204)
async def delete_product(
    product_id: int,
    session: AsyncSession = Depends(get_session),
    current: Staff = Depends(get_current_staff),
):
    """Удалить товар."""
    svc = ProductService(session, current.tenant_id)
    await svc.delete(product_id)
