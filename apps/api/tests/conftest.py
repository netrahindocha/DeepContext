import asyncio
import uuid
from collections.abc import Callable, Generator

import pytest
from fastapi.testclient import TestClient

from app.db.session import engine
from app.main import app


@pytest.fixture
def client() -> Generator[TestClient]:
    with TestClient(app) as test_client:
        yield test_client

    asyncio.run(engine.dispose())


@pytest.fixture
def register_and_login() -> Callable[[TestClient], tuple[str, str]]:
    def _register_and_login(client: TestClient) -> tuple[str, str]:
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

    return _register_and_login


@pytest.fixture
def create_workspace() -> Callable[[TestClient, str, str], dict]:
    def _create_workspace(client: TestClient, token: str, name: str) -> dict:
        response = client.post(
            "/api/v1/workspaces",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "name": name,
                "description": f"{name} description",
            },
        )

        assert response.status_code == 201
        return response.json()

    return _create_workspace
