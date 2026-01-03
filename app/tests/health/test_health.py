import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

from app.db.postgres import get_db_session
from app.db.redis import get_redis_client
from app.main import app

client = TestClient(app)


@pytest.mark.asyncio
async def test_redis_connection_health():
    redis_client = await get_redis_client()
    response = await redis_client.ping()
    assert response == True


@pytest.mark.asyncio
async def test_postgresql_connection_health(init_db_for_tests):
    async for session in get_db_session():
        response = await session.execute(text("SELECT 1"))
        assert response.scalar() == 1


def test_health_check():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"statusCode": 200, "detail": "ok", "result": "working"}
