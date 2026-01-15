from contextlib import asynccontextmanager

import httpx
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi_cache import FastAPICache
from fastapi_cache.backends.redis import RedisBackend
from redis.asyncio import Redis as AsyncRedis

from src.auth.router import auth_router, users_router
from src.company.router import companies_router, invitations_router, requests_router
from src.core.config import settings
from src.core.database import db_session_manager
from src.core.http_client import http_client_manager
from src.core.logger import logger
from src.core.redis import redis_manager
from src.quiz.router import attempt_router, quiz_router


# From guide https://medium.com/@tclaitken/setting-up-a-fastapi-app-with-async-sqlalchemy-2-0-pydantic-v2-e6c540be4308
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Startup")

    db_session_manager.start(str(settings.DB.DATABASE_URL), pool_size=20, max_overflow=10)
    redis_manager.start(str(settings.REDIS.REDIS_URL),
                        encoding="utf8", decode_responses=True, max_connections=20)

    redis_client = AsyncRedis(connection_pool=redis_manager.pool, encoding="utf8", decode_responses=True)
    FastAPICache.init(RedisBackend(redis_client), prefix="api-cache")

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
        "src.main:app",
        host=settings.APP.HOST,
        port=settings.APP.PORT,
        reload=settings.APP.RELOAD,
    )
