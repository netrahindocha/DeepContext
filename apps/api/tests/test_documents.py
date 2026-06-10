import uuid

from fastapi.testclient import TestClient


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


def test_create_document_returns_created_document(
    client: TestClient,
    register_and_login,
    create_workspace,
) -> None:
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


def test_create_document_rejects_invalid_source_type(
    client: TestClient,
    register_and_login,
    create_workspace,
) -> None:
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


def test_create_document_rejects_empty_title(
    client: TestClient,
    register_and_login,
    create_workspace,
) -> None:
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
    register_and_login,
    create_workspace,
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


def test_create_document_returns_404_for_missing_workspace(
    client: TestClient,
    register_and_login,
) -> None:
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
    register_and_login,
    create_workspace,
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
    register_and_login,
    create_workspace,
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


def test_list_documents_returns_404_for_missing_workspace(
    client: TestClient,
    register_and_login,
) -> None:
    _, token = register_and_login(client)
    workspace_id = uuid.uuid4()

    response = client.get(
        f"/api/v1/workspaces/{workspace_id}/documents",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "Workspace not found"}
