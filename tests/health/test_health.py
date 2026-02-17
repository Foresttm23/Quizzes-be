import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

from src.core.database import db_session_manager
from src.core.redis import redis_manager
from src.main import app

client = TestClient(app)


@pytest.mark.asyncio
async def test_redis_connection_health():
    async with redis_manager.session() as conn:
        response = await conn.ping()
        assert response


@pytest.mark.asyncio
async def test_postgresql_connection_health():
    async with db_session_manager.session() as session:
        response = await session.execute(text("SELECT 1"))
        assert response.scalar() == 1


def test_health_check():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"statusCode": 200, "detail": "ok", "result": "working"}
