from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI
import uvicorn

from .routers.health import router as health_router

app = FastAPI()

app.include_router(health_router)

origins = [
    "http://localhost:8000",
    "http://127.0.0.1:8000",
    "http://other.com"
    "https://other.com"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

if __name__ == '__main__':
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)
