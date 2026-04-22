from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_session
from app.models.staff import Staff, StaffRole
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
    password: str


class LoginResponse(BaseModel):
    token: str
    role: str
    username: str


class StaffCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=64)
    password: str = Field(..., min_length=6)
    role: StaffRole = StaffRole.operator


class StaffRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    username: str
    role: StaffRole


class StaffUpdate(BaseModel):
    password: str | None = Field(None, min_length=6)
    role: StaffRole | None = None


# ── Эндпоинты ────────────────────────────────────────────────

@router.post("/login", response_model=LoginResponse)
async def login(data: LoginRequest, session: AsyncSession = Depends(get_session)):
    result = await session.execute(select(Staff).where(Staff.username == data.username))
    staff = result.scalar_one_or_none()
    if not staff or not verify_password(data.password, staff.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Неверный логин или пароль")
    return LoginResponse(
        token=create_token(staff.id, staff.role),
        role=staff.role,
        username=staff.username,
    )


@router.get("/me", response_model=StaffRead)
async def get_me(current: Staff = Depends(get_current_staff)):
    return current


@router.get("/", response_model=list[StaffRead])
async def list_staff(
    session: AsyncSession = Depends(get_session),
    _: Staff = Depends(require_admin),
):
    result = await session.execute(select(Staff).order_by(Staff.created_at))
    return list(result.scalars().all())


@router.post("/", response_model=StaffRead, status_code=201)
async def create_staff(
    data: StaffCreate,
    session: AsyncSession = Depends(get_session),
    _: Staff = Depends(require_admin),
):
    existing = await session.execute(select(Staff).where(Staff.username == data.username))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Пользователь с таким именем уже существует")
    staff = Staff(
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
    result = await session.execute(select(Staff).where(Staff.id == staff_id))
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
    result = await session.execute(select(Staff).where(Staff.id == staff_id))
    staff = result.scalar_one_or_none()
    if not staff:
        raise HTTPException(status_code=404, detail="Не найден")
    await session.delete(staff)
    await session.flush()


class SetupRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=64)
    password: str = Field(..., min_length=6)


@router.post("/setup", response_model=LoginResponse, status_code=201)
async def setup_first_admin(data: SetupRequest, session: AsyncSession = Depends(get_session)):
    """Создаёт первого admin — только если таблица staff пуста."""
    existing = await session.execute(select(Staff))
    if existing.scalars().first() is not None:
        raise HTTPException(status_code=400, detail="Первичная настройка уже выполнена")
    staff = Staff(
        username=data.username,
        password_hash=hash_password(data.password),
        role=StaffRole.admin,
    )
    session.add(staff)
    await session.flush()
    await session.refresh(staff)
    return LoginResponse(
        token=create_token(staff.id, staff.role),
        role=staff.role,
        username=staff.username,
    )
