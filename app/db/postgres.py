from sqlalchemy.orm import declarative_base
from typing import Any, AsyncIterator
from typing import Annotated
from fastapi import Depends
import contextlib

from app.config import settings
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

Base = declarative_base()


# From guide https://medium.com/@tclaitken/setting-up-a-fastapi-app-with-async-sqlalchemy-2-0-pydantic-v2-e6c540be4308
class DBSessionManager:
    def __init__(self, host: str, engine_kwargs: dict[str, Any] | None = None):
        self._engine = create_async_engine(host, **(engine_kwargs or {}))
        self._sessionmaker = async_sessionmaker(autocommit=False, bind=self._engine, expire_on_commit=False)

    async def close(self):
        if self._engine:
            await self._engine.dispose()
            self._engine = None
            self._sessionmaker = None

    @contextlib.asynccontextmanager
    async def session(self) -> AsyncIterator[AsyncSession]:
        if self._sessionmaker is None:
            raise Exception("DBSessionManager is not initialized")

        session = self._sessionmaker()
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


sessionmanager = DBSessionManager(settings.database_url, {"echo": settings.echo_sql})


async def get_db_session():
    async with sessionmanager.session() as session:
        yield session


DBSessionDep = Annotated[AsyncSession, Depends(get_db_session)]
