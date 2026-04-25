from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_session
from app.config import settings
from app.models.staff import Staff, StaffRole

ALGORITHM = "HS256"

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
bearer_scheme = HTTPBearer(auto_error=False)


# ── Виртуальный объект для superadmin (нет записи в БД) ──────────
@dataclass
class SuperadminContext:
    id: None = None
    tenant_id: None = None
    username: str = "superadmin"
    role: str = "superadmin"


# ── Пароли ───────────────────────────────────────────────────────

def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


# ── JWT ──────────────────────────────────────────────────────────

def create_token(staff_id: int | None, role: str, tenant_id: int | None) -> str:
    expire = datetime.now(timezone.utc) + timedelta(hours=settings.TOKEN_EXPIRE_HOURS)
    return jwt.encode(
        {
            "sub": str(staff_id) if staff_id is not None else "superadmin",
            "role": role,
            "tenant_id": tenant_id,
            "exp": expire,
        },
        settings.SECRET_KEY,
        algorithm=ALGORITHM,
    )


def _decode_token(token: str) -> dict:
    try:
        return jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")


# ── Зависимости ──────────────────────────────────────────────────

async def get_current_staff(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    session: AsyncSession = Depends(get_session),
) -> Staff:
    """Возвращает Staff из БД. Superadmin через этот путь не проходит."""
    if not credentials:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    payload = _decode_token(credentials.credentials)
    if payload.get("role") == "superadmin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Use superadmin endpoint")
    try:
        staff_id = int(payload["sub"])
    except (KeyError, ValueError):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    result = await session.execute(select(Staff).where(Staff.id == staff_id))
    staff = result.scalar_one_or_none()
    if staff is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Staff not found")
    return staff


async def require_admin(staff: Staff = Depends(get_current_staff)) -> Staff:
    if staff.role != StaffRole.admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin only")
    return staff


async def require_superadmin(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> SuperadminContext:
    """Проверяет что токен принадлежит superadmin."""
    if not credentials:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    payload = _decode_token(credentials.credentials)
    if payload.get("role") != "superadmin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Superadmin only")
    return SuperadminContext()
