from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.db.postgres import sessionmanager
from app.db.redis import redis_client, pool
from app.routers.health import router as health_router


# From guide https://medium.com/@tclaitken/setting-up-a-fastapi-app-with-async-sqlalchemy-2-0-pydantic-v2-e6c540be4308
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup

    yield
    # Shutdown
    ## Close Redis pool and conn
    await redis_client.close()
    await pool.disconnect()
    ## Close the DB connection
    await sessionmanager.close()


app = FastAPI(lifespan=lifespan)

app.include_router(health_router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.app.origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

if __name__ == '__main__':
    uvicorn.run("app.main:app", host=settings.app.host, port=settings.app.port, reload=settings.app.reload)
