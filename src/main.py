from contextlib import asynccontextmanager

import httpx
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .auth.router import auth_router, users_router
from .company.router import companies_router, invitations_router, requests_router
from .core.config import settings
from .core.database import DBSessionManager
from .core.http_client import HTTPClientManager
from .core.logger import logger
from .core.redis import RedisManager
from .quiz.router import attempt_router, quiz_router


# From guide https://medium.com/@tclaitken/setting-up-a-fastapi-app-with-async-sqlalchemy-2-0-pydantic-v2-e6c540be4308
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Startup")

    db_session_manager = DBSessionManager()
    db_session_manager.start(str(settings.DB.DATABASE_URL), pool_size=20, max_overflow=10)

    redis_manager = RedisManager()
    redis_manager.start(str(settings.REDIS.REDIS_URL),
                        encoding="utf8", decode_responses=True, max_connections=20)

    http_client_manager = HTTPClientManager()
    http_client_manager.start(timeout=httpx.Timeout(10.0),
                              limits=httpx.Limits(max_connections=100, max_keepalive_connections=20))

    yield
    # Shutdown
    logger.info("Shutdown")

    await redis_manager.stop()
    await db_session_manager.stop()
    await http_client_manager.stop()


app = FastAPI(lifespan=lifespan)

app.include_router(auth_router)
app.include_router(users_router)
app.include_router(requests_router)
app.include_router(companies_router)
app.include_router(invitations_router)
app.include_router(quiz_router)
app.include_router(attempt_router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.APP.ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

if __name__ == "__main__":
    uvicorn.run(
        ".main:app",
        host=settings.APP.HOST,
        port=settings.APP.PORT,
        reload=settings.APP.RELOAD,
    )
