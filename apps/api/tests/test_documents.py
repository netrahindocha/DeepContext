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


def create_workspace(client: TestClient, token: str, name: str) -> dict:
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


def test_create_document_requires_authentication(client: TestClient) -> None:
    workspace_id = uuid.uuid4()

    response = client.post(
        f"/api/v1/workspaces/{workspace_id}/documents",
        json={
            "title": "Project Notes",
            "source_type": "text",
        },
    )

    assert response.status_code == 401
    assert response.json() == {"detail": "Not authenticated"}


def test_create_document_returns_created_document(client: TestClient) -> None:
    _, token = register_and_login(client)
    workspace = create_workspace(client, token, "Project Workspace")

    response = client.post(
        f"/api/v1/workspaces/{workspace['id']}/documents",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "title": "Project Notes",
            "source_type": "text",
        },
    )

    assert response.status_code == 201
    data = response.json()

    assert data["workspace_id"] == workspace["id"]
    assert data["owner_id"] == workspace["owner_id"]
    assert data["title"] == "Project Notes"
    assert data["source_type"] == "text"
    assert data["status"] == "pending"
    assert data["error_message"] is None
    assert "id" in data
    assert "created_at" in data
    assert "updated_at" in data


def test_create_document_rejects_invalid_source_type(client: TestClient) -> None:
    _, token = register_and_login(client)
    workspace = create_workspace(client, token, "Project Workspace")

    response = client.post(
        f"/api/v1/workspaces/{workspace['id']}/documents",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "title": "Project Notes",
            "source_type": "pdf",
        },
    )

    assert response.status_code == 422


def test_create_document_rejects_empty_title(client: TestClient) -> None:
    _, token = register_and_login(client)
    workspace = create_workspace(client, token, "Project Workspace")

    response = client.post(
        f"/api/v1/workspaces/{workspace['id']}/documents",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "title": "",
            "source_type": "text",
        },
    )

    assert response.status_code == 422


def test_create_document_returns_404_for_another_users_workspace(
    client: TestClient,
) -> None:
    _, owner_token = register_and_login(client)
    _, other_token = register_and_login(client)

    workspace = create_workspace(client, owner_token, "Private Workspace")

    response = client.post(
        f"/api/v1/workspaces/{workspace['id']}/documents",
        headers={"Authorization": f"Bearer {other_token}"},
        json={
            "title": "Unauthorized Notes",
            "source_type": "text",
        },
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "Workspace not found"}


def test_create_document_returns_404_for_missing_workspace(client: TestClient) -> None:
    _, token = register_and_login(client)
    workspace_id = uuid.uuid4()

    response = client.post(
        f"/api/v1/workspaces/{workspace_id}/documents",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "title": "Project Notes",
            "source_type": "text",
        },
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "Workspace not found"}


def test_list_documents_requires_authentication(client: TestClient) -> None:
    workspace_id = uuid.uuid4()

    response = client.get(f"/api/v1/workspaces/{workspace_id}/documents")

    assert response.status_code == 401
    assert response.json() == {"detail": "Not authenticated"}


def test_list_documents_returns_documents_for_workspace_owner(
    client: TestClient,
) -> None:
    _, token = register_and_login(client)
    workspace = create_workspace(client, token, "Project Workspace")

    create_response = client.post(
        f"/api/v1/workspaces/{workspace['id']}/documents",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "title": "Project Notes",
            "source_type": "markdown",
        },
    )
    assert create_response.status_code == 201

    response = client.get(
        f"/api/v1/workspaces/{workspace['id']}/documents",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    data = response.json()

    assert len(data) == 1
    assert data[0]["title"] == "Project Notes"
    assert data[0]["source_type"] == "markdown"
    assert data[0]["workspace_id"] == workspace["id"]


def test_list_documents_returns_404_for_another_users_workspace(
    client: TestClient,
) -> None:
    _, owner_token = register_and_login(client)
    _, other_token = register_and_login(client)

    workspace = create_workspace(client, owner_token, "Private Workspace")

    response = client.get(
        f"/api/v1/workspaces/{workspace['id']}/documents",
        headers={"Authorization": f"Bearer {other_token}"},
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "Workspace not found"}


def test_list_documents_returns_404_for_missing_workspace(client: TestClient) -> None:
    _, token = register_and_login(client)
    workspace_id = uuid.uuid4()

    response = client.get(
        f"/api/v1/workspaces/{workspace_id}/documents",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "Workspace not found"}
