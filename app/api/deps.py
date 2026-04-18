from typing import AsyncGenerator

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db

# Re-export для удобного импорта в роутерах
DbSession = Depends(get_db)


async def get_session(session: AsyncSession = Depends(get_db)) -> AsyncGenerator[AsyncSession, None]:
    yield session
