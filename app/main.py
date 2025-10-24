from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from fastapi import FastAPI
import uvicorn

from app.routers.health import router as health_router
from app.db.redis import redis_client, pool
from app.db.postgres import sessionmanager
from app.config import settings


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
    allow_origins=settings.origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

if __name__ == '__main__':
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)
