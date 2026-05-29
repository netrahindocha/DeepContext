from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_health_check_returns_ok() -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_readiness_check_returns_ready_when_database_available(monkeypatch) -> None:
    async def fake_check_database_connection(engine) -> bool:
        return True

    monkeypatch.setattr(
        "app.modules.health.router.check_database_connection",
        fake_check_database_connection,
    )

    response = client.get("/ready")

    assert response.status_code == 200
    assert response.json() == {"status": "ready", "database": "available"}


def test_readiness_check_returns_503_when_database_unavailable(monkeypatch) -> None:
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
