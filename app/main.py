import logging
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
import app.core.logger
from app.core.config import settings
from app.db.postgres import sessionmanager
from app.db.redis import redis_client, pool
from app.routers.health import router as health_router
from app.db.redis import redis_client, pool
from app.routers.health import router as health_router

logger = logging.getLogger(__name__)


# From guide https://medium.com/@tclaitken/setting-up-a-fastapi-app-with-async-sqlalchemy-2-0-pydantic-v2-e6c540be4308
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.debug(f"Startup")

    yield
    # Shutdown
    logger.debug(f"Shutdown")
    ## Close Redis pool and conn
    await redis_client.close()
    await pool.disconnect()
    ## Close the DB connection
    await sessionmanager.close()


app = FastAPI(lifespan=lifespan)

app.include_router(health_router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.APP.ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

if __name__ == '__main__':
    uvicorn.run("app.main:app", host=settings.APP.HOST, port=settings.APP.PORT, reload=settings.APP.RELOAD)
