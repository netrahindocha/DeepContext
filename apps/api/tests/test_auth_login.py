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


def test_login_returns_access_token_for_valid_credentials(client: TestClient) -> None:
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
    data = login_response.json()

    assert data["token_type"] == "bearer"
    assert isinstance(data["access_token"], str)
    assert data["access_token"]


def test_login_rejects_wrong_password(client: TestClient) -> None:
    email = f"user-{uuid.uuid4()}@example.com"

    register_response = client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": "strongpassword123",
        },
    )

    assert register_response.status_code == 201

    login_response = client.post(
        "/api/v1/auth/login",
        json={
            "email": email,
            "password": "wrongpassword123",
        },
    )

    assert login_response.status_code == 401
    assert login_response.json() == {"detail": "Invalid email or password"}


def test_login_rejects_unknown_email(client: TestClient) -> None:
    login_response = client.post(
        "/api/v1/auth/login",
        json={
            "email": f"missing-{uuid.uuid4()}@example.com",
            "password": "strongpassword123",
        },
    )

    assert login_response.status_code == 401
    assert login_response.json() == {"detail": "Invalid email or password"}
