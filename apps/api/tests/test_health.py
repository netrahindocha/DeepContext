import pytest
from sqlalchemy.exc import SQLAlchemyError

from fastapi.testclient import TestClient


def test_health_check_returns_ok(client: TestClient) -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_readiness_check_returns_ready_when_database_available(
    client: TestClient, monkeypatch
) -> None:
    async def fake_check_database_connection(engine) -> bool:
        return True

    monkeypatch.setattr(
        "app.modules.health.router.check_database_connection",
        fake_check_database_connection,
    )

    response = client.get("/ready")

    assert response.status_code == 200
    assert response.json() == {"status": "ready", "database": "available"}


def test_readiness_check_returns_503_when_database_unavailable(
    client: TestClient, monkeypatch
) -> None:
    async def fake_check_database_connection(engine) -> bool:
        return False

    monkeypatch.setattr(
        "app.modules.health.router.check_database_connection",
        fake_check_database_connection,
    )

    response = client.get("/ready")

    assert response.status_code == 503
    assert response.json() == {
        "status": "not_ready",
        "database": "unavailable",
    }


@pytest.mark.anyio
async def test_check_database_connection_returns_false_on_database_error() -> None:
    from app.db.health import check_database_connection

    class BrokenEngine:
        def connect(self):
            raise SQLAlchemyError("database unavailable")

    assert await check_database_connection(BrokenEngine()) is False


@pytest.mark.anyio
async def test_check_database_connection_returns_false_on_network_error() -> None:
    from app.db.health import check_database_connection

    class BrokenEngine:
        def connect(self):
            raise OSError("network unavailable")

    assert await check_database_connection(BrokenEngine()) is False
