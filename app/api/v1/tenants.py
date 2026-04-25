"""
Tenant management — только для superadmin.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_session
from app.models.staff import Staff, StaffRole
from app.models.tenant import Tenant
from app.services.auth import (
    SuperadminContext,
    create_token,
    hash_password,
    require_superadmin,
)

router = APIRouter(prefix="/tenants", tags=["Tenants (superadmin)"])


# ── Схемы ────────────────────────────────────────────────────────

class TenantCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    slug: str = Field(..., min_length=1, max_length=100, pattern=r"^[a-z0-9_-]+$")


class TenantUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=255)
    slug: str | None = Field(None, min_length=1, max_length=100, pattern=r"^[a-z0-9_-]+$")
    is_active: bool | None = None


class TenantRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    slug: str
    is_active: bool


class FirstAdminCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=64)
    password: str = Field(..., min_length=6, max_length=72)


class FirstAdminResponse(BaseModel):
    token: str
    role: str
    username: str
    tenant_id: int


# ── Эндпоинты ────────────────────────────────────────────────────

@router.get("", response_model=list[TenantRead])
async def list_tenants(
    session: AsyncSession = Depends(get_session),
    _: SuperadminContext = Depends(require_superadmin),
):
    result = await session.execute(select(Tenant).order_by(Tenant.id))
    return list(result.scalars().all())


@router.post("", response_model=TenantRead, status_code=201)
async def create_tenant(
    data: TenantCreate,
    session: AsyncSession = Depends(get_session),
    _: SuperadminContext = Depends(require_superadmin),
):
    existing = await session.execute(select(Tenant).where(Tenant.slug == data.slug))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Slug уже занят")
    tenant = Tenant(name=data.name, slug=data.slug)
    session.add(tenant)
    await session.flush()
    await session.refresh(tenant)
    return tenant


@router.get("/{tenant_id}", response_model=TenantRead)
async def get_tenant(
    tenant_id: int,
    session: AsyncSession = Depends(get_session),
    _: SuperadminContext = Depends(require_superadmin),
):
    tenant = await session.get(Tenant, tenant_id)
    if not tenant:
        raise HTTPException(status_code=404, detail="Тенант не найден")
    return tenant


@router.patch("/{tenant_id}", response_model=TenantRead)
async def update_tenant(
    tenant_id: int,
    data: TenantUpdate,
    session: AsyncSession = Depends(get_session),
    _: SuperadminContext = Depends(require_superadmin),
):
    tenant = await session.get(Tenant, tenant_id)
    if not tenant:
        raise HTTPException(status_code=404, detail="Тенант не найден")
    if data.name is not None:
        tenant.name = data.name
    if data.slug is not None:
        existing = await session.execute(
            select(Tenant).where(Tenant.slug == data.slug, Tenant.id != tenant_id)
        )
        if existing.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="Slug уже занят")
        tenant.slug = data.slug
    if data.is_active is not None:
        tenant.is_active = data.is_active
    await session.flush()
    return tenant


@router.delete("/{tenant_id}", status_code=204)
async def delete_tenant(
    tenant_id: int,
    session: AsyncSession = Depends(get_session),
    _: SuperadminContext = Depends(require_superadmin),
):
    tenant = await session.get(Tenant, tenant_id)
    if not tenant:
        raise HTTPException(status_code=404, detail="Тенант не найден")
    await session.delete(tenant)
    await session.flush()


@router.post("/{tenant_id}/staff", response_model=FirstAdminResponse, status_code=201)
async def create_first_admin(
    tenant_id: int,
    data: FirstAdminCreate,
    session: AsyncSession = Depends(get_session),
    _: SuperadminContext = Depends(require_superadmin),
):
    """Superadmin создаёт первого admin для тенанта."""
    tenant = await session.get(Tenant, tenant_id)
    if not tenant:
        raise HTTPException(status_code=404, detail="Тенант не найден")

    existing = await session.execute(
        select(Staff).where(Staff.tenant_id == tenant_id, Staff.username == data.username)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Пользователь с таким именем уже существует")

    staff = Staff(
        tenant_id=tenant_id,
        username=data.username,
        password_hash=hash_password(data.password),
        role=StaffRole.admin,
    )
    session.add(staff)
    await session.flush()
    await session.refresh(staff)

    return FirstAdminResponse(
        token=create_token(staff.id, staff.role, tenant_id),
        role=staff.role,
        username=staff.username,
        tenant_id=tenant_id,
    )
