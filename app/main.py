from fastapi import FastAPI
import uvicorn

from .routers.health import router as health_router

app = FastAPI()

app.include_router(health_router)

if __name__ == '__main__':
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)
