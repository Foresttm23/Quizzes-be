import contextlib
import uuid
from typing import Any, AsyncIterator, AsyncGenerator

from sqlalchemy import UUID
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.orm import Mapped, mapped_column

from app.core.exceptions import DBSessionNotInitializedException
from app.core.logger import logger


class Base(DeclarativeBase):
    __mapper_args__ = {"eager_defaults": True}
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)


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
            raise DBSessionNotInitializedException()

        session = self._sessionmaker()
        try:
            yield session
        except Exception:
            logger.error("DB session failed, rolling back", exc_info=True)
            await session.rollback()
            raise
        finally:
            await session.close()


sessionmanager: DBSessionManager | None = None


def init_db(database_url: str, engine_kwargs: dict[str, Any] | None = None):
    global sessionmanager
    sessionmanager = DBSessionManager(database_url, engine_kwargs or {})
    return sessionmanager


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    async with sessionmanager.session() as session:
        yield session
