from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI
import uvicorn

from .routers.health import router as health_router
from .config import settings

app = FastAPI()

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
