from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.logger import logger
from app.db.postgres import init_db
from app.db.redis import redis_client, pool
from app.routers.health_router import router as health_router
from routers.auth.auth_router import router as auth_router
from routers.company.company_router import router as company_router
from routers.company.invitation_router import router as invitation_router
from routers.company.join_request_router import router as company_join_request_router
from routers.company.member_router import router as company_member_router
from routers.company.quiz.quiz_router import router as company_quiz_router
from routers.user.user_router import router as user_router


# From guide https://medium.com/@tclaitken/setting-up-a-fastapi-app-with-async-sqlalchemy-2-0-pydantic-v2-e6c540be4308
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Startup")
    sessionmanager = init_db(settings.DB.DATABASE_URL)

    yield
    # Shutdown
    logger.info("Shutdown")
    await redis_client.aclose()
    await pool.disconnect()
    await sessionmanager.close()


app = FastAPI(lifespan=lifespan)

app.include_router(health_router)
app.include_router(user_router)
app.include_router(auth_router)
app.include_router(company_router)
app.include_router(company_member_router)
app.include_router(invitation_router)
app.include_router(company_join_request_router)
app.include_router(company_quiz_router)

app.add_middleware(CORSMiddleware, allow_origins=settings.APP.ORIGINS, allow_credentials=True, allow_methods=["*"],
                   allow_headers=["*"], )

if __name__ == "__main__":
    uvicorn.run("app.main:app", host=settings.APP.HOST, port=settings.APP.PORT, reload=settings.APP.RELOAD, )
