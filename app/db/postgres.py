import contextlib
import logging
from typing import Any, AsyncIterator, AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import declarative_base

from app.core.config import settings

logger = logging.getLogger(__name__)

Base = declarative_base()


# From guide https://medium.com/@tclaitken/setting-up-a-fastapi-app-with-async-sqlalchemy-2-0-pydantic-v2-e6c540be4308
class DBSessionManager:
    def __init__(self, database_url: str, engine_kwargs: dict[str, Any] | None = None):
        self._engine = create_async_engine(database_url, **(engine_kwargs or {}))
        self._sessionmaker = async_sessionmaker(autocommit=False, bind=self._engine, expire_on_commit=False)

    async def close(self) -> None:
        if self._engine:
            await self._engine.dispose()
            self._engine = None
            self._sessionmaker = None

    @contextlib.asynccontextmanager
    async def session(self) -> AsyncIterator[AsyncSession]:
        if self._sessionmaker is None:
            message = "DBSessionManager is not initialized!"
            logger.error(message)
            raise Exception(message)

        session = self._sessionmaker()
        try:
            yield session
        except Exception:
            logger.error("DB session failed, rolling back", exc_info=True)
            await session.rollback()
            raise
        finally:
            await session.close()


sessionmanager = DBSessionManager(settings.DB.DATABASE_URL, {"echo": settings.DB.ECHO_SQL})


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    async with sessionmanager.session() as session:
        yield session
