from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.auth.router import auth_router, users_router
from src.company.router import companies_router, invitations_router, requests_router
from src.core.config import settings
from src.core.database import init_db
from src.core.logger import logger
from src.core.redis import init_redis
from src.quiz.router import attempt_router, quiz_router


# From guide https://medium.com/@tclaitken/setting-up-a-fastapi-app-with-async-sqlalchemy-2-0-pydantic-v2-e6c540be4308
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Startup")
    sessionmanager = init_db(str(settings.DB.DATABASE_URL), {"pool_size": 20})
    redis_pool = init_redis(
        str(settings.REDIS.REDIS_URL),
        {"encoding": "utf8", "decode_responses": True, "max_connections": 20},
    )

    yield
    # Shutdown
    logger.info("Shutdown")
    if redis_pool:
        await redis_pool.disconnect()
    if sessionmanager:
        await sessionmanager.close()


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
        "src.main:src",
        host=settings.APP.HOST,
        port=settings.APP.PORT,
        reload=settings.APP.RELOAD,
    )
