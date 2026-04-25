from typing import AsyncGenerator, Optional

from fastapi import Depends, HTTPException, Query, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db

# Re-export для удобного импорта в роутерах
DbSession = Depends(get_db)

_optional_bearer = HTTPBearer(auto_error=False)


async def get_session(session: AsyncSession = Depends(get_db)) -> AsyncGenerator[AsyncSession, None]:
    yield session


async def resolve_tenant_id(
    tenant_id: Optional[int] = Query(None, description="ID тенанта (для мини-аппа)"),
    credentials: HTTPAuthorizationCredentials | None = Depends(_optional_bearer),
) -> int:
    """
    Определяет tenant_id для публичных/полупубличных эндпоинтов.
    Приоритет: JWT tenant_id → query param tenant_id → 400 (нет fallback на 1).

    - Админ/оператор: авторизован через JWT, tenant_id берётся оттуда.
    - Мини-апп: без JWT, передаёт tenant_id явно как query param.
    """
    if credentials:
        try:
            payload = jwt.decode(
                credentials.credentials,
                settings.SECRET_KEY,
                algorithms=["HS256"],
            )
            tid = payload.get("tenant_id")
            if tid is not None:
                return int(tid)
        except (JWTError, Exception):
            pass
    if tenant_id is not None:
        return tenant_id
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="tenant_id is required",
    )
