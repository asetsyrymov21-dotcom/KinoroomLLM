from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_session
from app.repositories.user import UserRepository
from app.schemas.user import UserCreate, UserRead, UserUpdate

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/by-telegram/{telegram_id}", response_model=UserRead)
async def get_by_telegram(
    telegram_id: int,
    session: AsyncSession = Depends(get_session),
):
    """Найти пользователя по Telegram ID. Используется Mini App для авторизации."""
    repo = UserRepository(session)
    user = await repo.get_by_telegram_id(telegram_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user


@router.post("/", response_model=UserRead, status_code=201)
async def create_user(
    data: UserCreate,
    session: AsyncSession = Depends(get_session),
):
    """Создать или вернуть существующего пользователя по telegram_id."""
    repo = UserRepository(session)
    return await repo.get_or_create(
        telegram_id=data.telegram_id,
        name=data.name,
        phone=data.phone,
    )


@router.get("/{user_id}", response_model=UserRead)
async def get_user(
    user_id: int,
    session: AsyncSession = Depends(get_session),
):
    repo = UserRepository(session)
    user = await repo.get(user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user


@router.patch("/{user_id}/phone", response_model=UserRead)
async def update_phone(
    user_id: int,
    data: UserUpdate,
    session: AsyncSession = Depends(get_session),
):
    """Обновить номер телефона пользователя."""
    repo = UserRepository(session)
    user = await repo.update_phone(user_id, data.phone)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user
