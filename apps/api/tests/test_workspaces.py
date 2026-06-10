import uuid

from fastapi.testclient import TestClient


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


def test_create_workspace_returns_created_workspace(
    client: TestClient,
    register_and_login,
) -> None:
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
    register_and_login,
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


def test_create_workspace_rejects_empty_name(
    client: TestClient,
    register_and_login,
) -> None:
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


def test_get_workspace_returns_workspace_for_owner(
    client: TestClient,
    register_and_login,
    create_workspace,
) -> None:
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


def test_get_workspace_returns_404_for_missing_workspace(
    client: TestClient,
    register_and_login,
) -> None:
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
    register_and_login,
    create_workspace,
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


def test_update_workspace_updates_workspace_for_owner(
    client: TestClient,
    register_and_login,
    create_workspace,
) -> None:
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


def test_update_workspace_returns_404_for_missing_workspace(
    client: TestClient,
    register_and_login,
) -> None:
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
    register_and_login,
    create_workspace,
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


def test_update_workspace_rejects_empty_name(
    client: TestClient,
    register_and_login,
    create_workspace,
) -> None:
    _, token = register_and_login(client)
    created_workspace = create_workspace(client, token, "Original Workspace")

    response = client.patch(
        f"/api/v1/workspaces/{created_workspace['id']}",
        headers={"Authorization": f"Bearer {token}"},
        json={"name": ""},
    )

    assert response.status_code == 422


def test_update_workspace_ignores_owner_id(
    client: TestClient,
    register_and_login,
    create_workspace,
) -> None:
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


def test_delete_workspace_deletes_workspace_for_owner(
    client: TestClient,
    register_and_login,
    create_workspace,
) -> None:
    _, token = register_and_login(client)
    created_workspace = create_workspace(client, token, "Workspace to Delete")

    delete_response = client.delete(
        f"/api/v1/workspaces/{created_workspace['id']}",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert delete_response.status_code == 204
    assert delete_response.content == b""

    get_response = client.get(
        f"/api/v1/workspaces/{created_workspace['id']}",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert get_response.status_code == 404
    assert get_response.json() == {"detail": "Workspace not found"}


def test_delete_workspace_removes_workspace_from_list(
    client: TestClient,
    register_and_login,
    create_workspace,
) -> None:
    _, token = register_and_login(client)
    created_workspace = create_workspace(client, token, "Workspace to Delete")

    delete_response = client.delete(
        f"/api/v1/workspaces/{created_workspace['id']}",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert delete_response.status_code == 204

    list_response = client.get(
        "/api/v1/workspaces",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert list_response.status_code == 200
    assert list_response.json() == []


def test_delete_workspace_requires_authentication(client: TestClient) -> None:
    workspace_id = uuid.uuid4()

    response = client.delete(f"/api/v1/workspaces/{workspace_id}")

    assert response.status_code == 401
    assert response.json() == {"detail": "Not authenticated"}


def test_delete_workspace_returns_404_for_missing_workspace(
    client: TestClient,
    register_and_login,
) -> None:
    _, token = register_and_login(client)
    workspace_id = uuid.uuid4()

    delete_response = client.delete(
        f"/api/v1/workspaces/{workspace_id}",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert delete_response.status_code == 404
    assert delete_response.json() == {"detail": "Workspace not found"}


def test_delete_workspace_returns_404_for_another_users_workspace(
    client: TestClient,
    register_and_login,
    create_workspace,
) -> None:
    _, owner_token = register_and_login(client)
    _, other_token = register_and_login(client)

    created_workspace = create_workspace(client, owner_token, "Private Workspace")

    response = client.delete(
        f"/api/v1/workspaces/{created_workspace['id']}",
        headers={"Authorization": f"Bearer {other_token}"},
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "Workspace not found"}

    owner_get_response = client.get(
        f"/api/v1/workspaces/{created_workspace['id']}",
        headers={"Authorization": f"Bearer {owner_token}"},
    )

    assert owner_get_response.status_code == 200
