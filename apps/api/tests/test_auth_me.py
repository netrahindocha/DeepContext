import asyncio
import uuid
from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient

from app.db.session import engine
from app.main import app


@pytest.fixture
def client() -> Generator[TestClient]:
    with TestClient(app) as test_client:
        yield test_client

    asyncio.run(engine.dispose())


def register_and_login(client: TestClient) -> tuple[str, str]:
    email = f"user-{uuid.uuid4()}@example.com"
    password = "strongpassword123"

    register_response = client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": password,
        },
    )

    assert register_response.status_code == 201

    login_response = client.post(
        "/api/v1/auth/login",
        json={
            "email": email,
            "password": password,
        },
    )
    assert login_response.status_code == 200

    return email, login_response.json()["access_token"]


def test_me_returns_current_user_for_valid_token(client: TestClient) -> None:
    email, token = register_and_login(client)

    response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    data = response.json()

    assert data["email"] == email
    assert data["is_active"] is True
    assert "id" in data
    assert "hashed_password" not in data


def test_me_rejects_missing_token(client: TestClient) -> None:
    response = client.get("/api/v1/auth/me")

    assert response.status_code == 401
    assert response.json() == {"detail": "Not authenticated"}


def test_me_rejects_invalid_token(client: TestClient) -> None:
    response = client.get(
        "/api/v1/auth/me",
        headers={
            "Authorization": "Bearer not-a-valid-token",
        },
    )

    assert response.status_code == 401
    assert response.json() == {"detail": "Invalid authentication credentials"}
