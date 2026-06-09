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


def test_create_workspace_requires_authentication(client: TestClient) -> None:
    response = client.post(
        "/api/v1/workspaces",
        json={
            "name": "Project Notes",
            "description": "Private project workspace",
        },
    )

    assert response.status_code == 401
    assert response.json() == {"detail": "Not authenticated"}


def test_create_workspace_returns_created_workspace(client: TestClient) -> None:
    _, token = register_and_login(client)

    response = client.post(
        "/api/v1/workspaces",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "name": "Project Notes",
            "description": "Private project workspace",
        },
    )

    assert response.status_code == 201
    data = response.json()

    assert data["name"] == "Project Notes"
    assert data["description"] == "Private project workspace"
    assert "id" in data
    assert "owner_id" in data
    assert "created_at" in data
    assert "updated_at" in data


def test_list_workspaces_requires_authentication(client: TestClient) -> None:
    response = client.get("/api/v1/workspaces")

    assert response.status_code == 401
    assert response.json() == {"detail": "Not authenticated"}


def test_list_workspaces_returns_only_current_users_workspaces(
    client: TestClient,
) -> None:
    _, first_token = register_and_login(client)
    _, second_token = register_and_login(client)

    first_create_response = client.post(
        "/api/v1/workspaces",
        headers={"Authorization": f"Bearer {first_token}"},
        json={
            "name": "First User Workspace",
            "description": "Owned by first user",
        },
    )
    assert first_create_response.status_code == 201

    second_create_response = client.post(
        "/api/v1/workspaces",
        headers={"Authorization": f"Bearer {second_token}"},
        json={
            "name": "Second User Workspace",
            "description": "Owned by second user",
        },
    )
    assert second_create_response.status_code == 201

    first_list_response = client.get(
        "/api/v1/workspaces",
        headers={"Authorization": f"Bearer {first_token}"},
    )
    second_list_response = client.get(
        "/api/v1/workspaces",
        headers={"Authorization": f"Bearer {second_token}"},
    )

    assert first_list_response.status_code == 200
    assert second_list_response.status_code == 200

    first_workspaces = first_list_response.json()
    second_workspaces = second_list_response.json()

    assert len(first_workspaces) == 1
    assert len(second_workspaces) == 1

    assert first_workspaces[0]["name"] == "First User Workspace"
    assert second_workspaces[0]["name"] == "Second User Workspace"

    assert first_workspaces[0]["owner_id"] != second_workspaces[0]["owner_id"]


def test_create_workspace_rejects_empty_name(client: TestClient) -> None:
    _, token = register_and_login(client)

    response = client.post(
        "/api/v1/workspaces",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "name": "",
            "description": "Invalid workspace",
        },
    )

    assert response.status_code == 422


def test_get_workspace_returns_workspace_for_owner(client: TestClient) -> None:
    _, token = register_and_login(client)
    created_workspace = create_workspace(client, token, "Owner Workspace")

    response = client.get(
        f"/api/v1/workspaces/{created_workspace['id']}",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    data = response.json()

    assert data["id"] == created_workspace["id"]
    assert data["name"] == "Owner Workspace"
    assert data["owner_id"] == created_workspace["owner_id"]


def test_get_workspace_requires_authentication(client: TestClient) -> None:
    workspace_id = uuid.uuid4()

    response = client.get(f"/api/v1/workspaces/{workspace_id}")

    assert response.status_code == 401
    assert response.json() == {"detail": "Not authenticated"}


def test_get_workspace_returns_404_for_missing_workspace(client: TestClient) -> None:
    _, token = register_and_login(client)
    workspace_id = uuid.uuid4()

    response = client.get(
        f"/api/v1/workspaces/{workspace_id}",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "Workspace not found"}


def test_get_workspace_returns_404_for_another_users_workspace(
    client: TestClient,
) -> None:
    _, owner_token = register_and_login(client)
    _, other_token = register_and_login(client)

    created_workspace = create_workspace(
        client,
        owner_token,
        "Private Workspace",
    )

    response = client.get(
        f"/api/v1/workspaces/{created_workspace['id']}",
        headers={"Authorization": f"Bearer {other_token}"},
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "Workspace not found"}


def test_update_workspace_updates_workspace_for_owner(client: TestClient) -> None:
    _, token = register_and_login(client)
    created_workspace = create_workspace(client, token, "Original Workspace")

    response = client.patch(
        f"/api/v1/workspaces/{created_workspace['id']}",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "name": "Updated Workspace",
            "description": "Updated description",
        },
    )

    assert response.status_code == 200
    data = response.json()

    assert data["id"] == created_workspace["id"]
    assert data["name"] == "Updated Workspace"
    assert data["description"] == "Updated description"
    assert data["owner_id"] == created_workspace["owner_id"]


def test_update_workspace_requires_authentication(client: TestClient) -> None:
    workspace_id = uuid.uuid4()

    response = client.patch(
        f"/api/v1/workspaces/{workspace_id}",
        json={"name": "Updated Workspace"},
    )

    assert response.status_code == 401
    assert response.json() == {"detail": "Not authenticated"}


def test_update_workspace_returns_404_for_missing_workspace(client: TestClient) -> None:
    _, token = register_and_login(client)
    workspace_id = uuid.uuid4()

    response = client.patch(
        f"/api/v1/workspaces/{workspace_id}",
        headers={"Authorization": f"Bearer {token}"},
        json={"name": "Updated workspace"},
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "Workspace not found"}


def test_update_workspace_returns_404_for_another_users_workspace(
    client: TestClient,
) -> None:
    _, owner_token = register_and_login(client)
    _, other_token = register_and_login(client)

    created_workspace = create_workspace(
        client,
        owner_token,
        "Private Workspace",
    )

    response = client.patch(
        f"/api/v1/workspaces/{created_workspace['id']}",
        headers={"Authorization": f"Bearer {other_token}"},
        json={"name": "Unauthorized Update"},
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "Workspace not found"}


def test_update_workspace_rejects_empty_name(client: TestClient) -> None:
    _, token = register_and_login(client)
    created_workspace = create_workspace(client, token, "Original Workspace")

    response = client.patch(
        f"/api/v1/workspaces/{created_workspace['id']}",
        headers={"Authorization": f"Bearer {token}"},
        json={"name": ""},
    )

    assert response.status_code == 422


def test_update_workspace_ignores_owner_id(client: TestClient) -> None:
    _, token = register_and_login(client)
    created_workspace = create_workspace(client, token, "Original Workspace")

    response = client.patch(
        f"/api/v1/workspaces/{created_workspace['id']}",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "name": "Updated Workspace",
            "owner_id": str(uuid.uuid4()),
        },
    )

    assert response.status_code == 200
    assert response.json()["owner_id"] == created_workspace["owner_id"]
