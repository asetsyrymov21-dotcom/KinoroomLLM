from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_session
from app.config import settings
from app.models.staff import Staff, StaffRole
from app.models.tenant import Tenant
from app.services.auth import (
    create_token,
    get_current_staff,
    hash_password,
    require_admin,
    verify_password,
)

router = APIRouter(prefix="/staff", tags=["Staff"])


# ── Схемы ────────────────────────────────────────────────────

class LoginRequest(BaseModel):
    username: str
    password: str = Field(..., max_length=72)
    tenant_slug: str | None = Field(None, max_length=100)


class LoginResponse(BaseModel):
    token: str
    role: str
    username: str
    tenant_id: int | None = None


class StaffCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=64)
    password: str = Field(..., min_length=6, max_length=72)
    role: StaffRole = StaffRole.operator


class StaffRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    username: str
    role: StaffRole
    tenant_id: int


class StaffUpdate(BaseModel):
    password: str | None = Field(None, min_length=6, max_length=72)
    role: StaffRole | None = None


class SetupRequest(BaseModel):
    tenant_name: str = Field(..., min_length=1, max_length=255, description="Название организации")
    tenant_slug: str = Field(..., min_length=1, max_length=100, description="Slug тенанта (латиница, уникальный)")
    username: str = Field(..., min_length=3, max_length=64)
    password: str = Field(..., min_length=6, max_length=72)


# ── Эндпоинты ────────────────────────────────────────────────

@router.post("/login", response_model=LoginResponse)
async def login(data: LoginRequest, session: AsyncSession = Depends(get_session)):
    # Проверяем superadmin через env (нет записи в БД)
    if (
        data.username == settings.SUPERADMIN_USERNAME
        and data.password == settings.SUPERADMIN_PASSWORD
    ):
        return LoginResponse(
            token=create_token(None, "superadmin", None),
            role="superadmin",
            username=settings.SUPERADMIN_USERNAME,
            tenant_id=None,
        )

    query = select(Staff).where(Staff.username == data.username)
    if data.tenant_slug:
        query = query.join(Tenant, Tenant.id == Staff.tenant_id).where(Tenant.slug == data.tenant_slug)

    result = await session.execute(query.order_by(Staff.id).limit(2))
    matches = list(result.scalars().all())
    if len(matches) > 1:
        raise HTTPException(status_code=400, detail="Укажите tenant_slug для входа")

    staff = matches[0] if matches else None
    if not staff or not verify_password(data.password, staff.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Неверный логин или пароль")
    return LoginResponse(
        token=create_token(staff.id, staff.role, staff.tenant_id),
        role=staff.role,
        username=staff.username,
        tenant_id=staff.tenant_id,
    )


@router.get("/me", response_model=StaffRead)
async def get_me(current: Staff = Depends(get_current_staff)):
    return current


@router.get("", response_model=list[StaffRead])
async def list_staff(
    session: AsyncSession = Depends(get_session),
    current: Staff = Depends(require_admin),
):
    result = await session.execute(
        select(Staff)
        .where(Staff.tenant_id == current.tenant_id)
        .order_by(Staff.created_at)
    )
    return list(result.scalars().all())


@router.post("", response_model=StaffRead, status_code=201)
async def create_staff(
    data: StaffCreate,
    session: AsyncSession = Depends(get_session),
    current: Staff = Depends(require_admin),
):
    existing = await session.execute(
        select(Staff).where(
            Staff.tenant_id == current.tenant_id,
            Staff.username == data.username,
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Пользователь с таким именем уже существует")
    staff = Staff(
        tenant_id=current.tenant_id,
        username=data.username,
        password_hash=hash_password(data.password),
        role=data.role,
    )
    session.add(staff)
    await session.flush()
    await session.refresh(staff)
    return staff


@router.patch("/{staff_id}", response_model=StaffRead)
async def update_staff(
    staff_id: int,
    data: StaffUpdate,
    session: AsyncSession = Depends(get_session),
    current: Staff = Depends(require_admin),
):
    result = await session.execute(
        select(Staff).where(
            Staff.id == staff_id,
            Staff.tenant_id == current.tenant_id,
        )
    )
    staff = result.scalar_one_or_none()
    if not staff:
        raise HTTPException(status_code=404, detail="Не найден")
    if data.password:
        staff.password_hash = hash_password(data.password)
    if data.role is not None:
        # нельзя убрать роль admin у себя
        if staff.id == current.id and data.role != StaffRole.admin:
            raise HTTPException(status_code=400, detail="Нельзя снять с себя роль admin")
        staff.role = data.role
    await session.flush()
    return staff


@router.delete("/{staff_id}", status_code=204)
async def delete_staff(
    staff_id: int,
    session: AsyncSession = Depends(get_session),
    current: Staff = Depends(require_admin),
):
    if staff_id == current.id:
        raise HTTPException(status_code=400, detail="Нельзя удалить себя")
    result = await session.execute(
        select(Staff).where(
            Staff.id == staff_id,
            Staff.tenant_id == current.tenant_id,
        )
    )
    staff = result.scalar_one_or_none()
    if not staff:
        raise HTTPException(status_code=404, detail="Не найден")
    await session.delete(staff)
    await session.flush()


@router.post("/setup", response_model=LoginResponse, status_code=201)
async def setup_first_admin(data: SetupRequest, session: AsyncSession = Depends(get_session)):
    """
    Создаёт первый тенант (или обновляет дефолтный, созданный миграцией) и первого admin.
    Блокируется если уже есть хотя бы один admin.
    """
    # Блокируем если admin уже существует
    existing_admin = await session.execute(
        select(Staff).where(Staff.role == StaffRole.admin)
    )
    if existing_admin.scalars().first() is not None:
        raise HTTPException(status_code=400, detail="Первичная настройка уже выполнена")

    # Используем дефолтный тенант (созданный миграцией) или создаём новый
    existing_tenant = await session.execute(select(Tenant).limit(1))
    tenant = existing_tenant.scalar_one_or_none()

    if tenant is None:
        # Полностью чистая БД без миграционного тенанта
        tenant = Tenant(name=data.tenant_name, slug=data.tenant_slug)
        session.add(tenant)
        await session.flush()
        await session.refresh(tenant)
    else:
        # Обновляем дефолтный тенант реальными данными
        tenant.name = data.tenant_name
        tenant.slug = data.tenant_slug
        await session.flush()

    # Создать первого admin
    staff = Staff(
        tenant_id=tenant.id,
        username=data.username,
        password_hash=hash_password(data.password),
        role=StaffRole.admin,
    )
    session.add(staff)
    await session.flush()
    await session.refresh(staff)

    return LoginResponse(
        token=create_token(staff.id, staff.role, tenant.id),
        role=staff.role,
        username=staff.username,
        tenant_id=tenant.id,
    )
