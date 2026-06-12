import uuid

from fastapi.testclient import TestClient


def create_document(
    client: TestClient,
    token: str,
    workspace_id: str,
    title: str,
    source_type: str = "text",
    content: str = "Document body",
) -> dict:
    response = client.post(
        f"/api/v1/workspaces/{workspace_id}/documents",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "title": title,
            "source_type": source_type,
            "content": content,
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
            "content": "Raw project notes",
        },
    )

    assert response.status_code == 201
    data = response.json()

    assert data["workspace_id"] == workspace["id"]
    assert data["owner_id"] == workspace["owner_id"]
    assert data["title"] == "Project Notes"
    assert data["source_type"] == "text"
    assert data["status"] == "completed"
    assert data["error_message"] is None
    assert "content" not in data
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
            "content": "Raw unauthorized notes",
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
            "content": "Raw project notes",
        },
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "Workspace not found"}


def test_create_document_rejects_missing_content(
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

    assert response.status_code == 422


def test_create_document_rejects_empty_content(
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
            "content": "",
        },
    )

    assert response.status_code == 422


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
            "content": "Raw markdown notes",
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


def test_get_document_returns_document_for_workspace_owner(
    client: TestClient,
    register_and_login,
    create_workspace,
) -> None:
    _, token = register_and_login(client)
    workspace = create_workspace(client, token, "Project Workspace")
    document = create_document(client, token, workspace["id"], "Project Notes")

    response = client.get(
        f"/api/v1/workspaces/{workspace['id']}/documents/{document['id']}",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    data = response.json()

    assert data["id"] == document["id"]
    assert data["workspace_id"] == workspace["id"]
    assert data["owner_id"] == workspace["owner_id"]
    assert data["title"] == "Project Notes"


def test_get_document_requires_authentication(client: TestClient) -> None:
    workspace_id = uuid.uuid4()
    document_id = uuid.uuid4()

    response = client.get(f"/api/v1/workspaces/{workspace_id}/documents/{document_id}")

    assert response.status_code == 401
    assert response.json() == {"detail": "Not authenticated"}


def test_get_document_returns_404_for_missing_workspace(
    client: TestClient,
    register_and_login,
) -> None:
    _, token = register_and_login(client)
    workspace_id = uuid.uuid4()
    document_id = uuid.uuid4()

    response = client.get(
        f"/api/v1/workspaces/{workspace_id}/documents/{document_id}",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "Workspace not found"}


def test_get_document_returns_404_for_missing_document(
    client: TestClient,
    register_and_login,
    create_workspace,
) -> None:
    _, token = register_and_login(client)
    workspace = create_workspace(client, token, "Project Workspace")
    document_id = uuid.uuid4()

    response = client.get(
        f"/api/v1/workspaces/{workspace['id']}/documents/{document_id}",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "Document not found"}


def test_get_document_returns_404_for_another_users_workspace(
    client: TestClient,
    register_and_login,
    create_workspace,
) -> None:
    _, owner_token = register_and_login(client)
    _, other_token = register_and_login(client)

    workspace = create_workspace(client, owner_token, "Private Workspace")
    document = create_document(client, owner_token, workspace["id"], "Private Notes")

    response = client.get(
        f"/api/v1/workspaces/{workspace['id']}/documents/{document['id']}",
        headers={"Authorization": f"Bearer {other_token}"},
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "Workspace not found"}


def test_get_document_returns_404_for_document_in_another_workspace(
    client: TestClient,
    register_and_login,
    create_workspace,
) -> None:
    _, token = register_and_login(client)
    first_workspace = create_workspace(client, token, "First Workspace")
    second_workspace = create_workspace(client, token, "Second Workspace")
    document = create_document(
        client,
        token,
        first_workspace["id"],
        "First Workspace Notes",
    )

    response = client.get(
        f"/api/v1/workspaces/{second_workspace['id']}/documents/{document['id']}",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "Document not found"}


def test_update_document_updates_title_for_workspace_owner(
    client: TestClient,
    register_and_login,
    create_workspace,
) -> None:
    _, token = register_and_login(client)
    workspace = create_workspace(client, token, "Project Workspace")
    document = create_document(client, token, workspace["id"], "Original Notes")

    response = client.patch(
        f"/api/v1/workspaces/{workspace['id']}/documents/{document['id']}",
        headers={"Authorization": f"Bearer {token}"},
        json={"title": "Updated Notes"},
    )

    assert response.status_code == 200
    data = response.json()

    assert data["id"] == document["id"]
    assert data["title"] == "Updated Notes"
    assert data["workspace_id"] == workspace["id"]
    assert data["owner_id"] == workspace["owner_id"]
    assert data["source_type"] == document["source_type"]
    assert data["status"] == document["status"]


def test_update_document_requires_authentication(client: TestClient) -> None:
    workspace_id = uuid.uuid4()
    document_id = uuid.uuid4()

    response = client.patch(
        f"/api/v1/workspaces/{workspace_id}/documents/{document_id}",
        json={"title": "Updated Notes"},
    )

    assert response.status_code == 401
    assert response.json() == {"detail": "Not authenticated"}


def test_update_document_returns_404_for_missing_workspace(
    client: TestClient,
    register_and_login,
) -> None:
    _, token = register_and_login(client)
    workspace_id = uuid.uuid4()
    document_id = uuid.uuid4()

    response = client.patch(
        f"/api/v1/workspaces/{workspace_id}/documents/{document_id}",
        headers={"Authorization": f"Bearer {token}"},
        json={"title": "Updated Notes"},
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "Workspace not found"}


def test_update_document_returns_404_for_missing_document(
    client: TestClient,
    register_and_login,
    create_workspace,
) -> None:
    _, token = register_and_login(client)
    workspace = create_workspace(client, token, "Project Workspace")
    document_id = uuid.uuid4()

    response = client.patch(
        f"/api/v1/workspaces/{workspace['id']}/documents/{document_id}",
        headers={"Authorization": f"Bearer {token}"},
        json={"title": "Updated Notes"},
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "Document not found"}


def test_update_document_rejects_empty_title(
    client: TestClient,
    register_and_login,
    create_workspace,
) -> None:
    _, token = register_and_login(client)
    workspace = create_workspace(client, token, "Project Workspace")
    document = create_document(client, token, workspace["id"], "Original Notes")

    response = client.patch(
        f"/api/v1/workspaces/{workspace['id']}/documents/{document['id']}",
        headers={"Authorization": f"Bearer {token}"},
        json={"title": ""},
    )

    assert response.status_code == 422


def test_update_document_rejects_missing_title(
    client: TestClient,
    register_and_login,
    create_workspace,
) -> None:
    _, token = register_and_login(client)
    workspace = create_workspace(client, token, "Project Workspace")
    document = create_document(client, token, workspace["id"], "Original Notes")

    response = client.patch(
        f"/api/v1/workspaces/{workspace['id']}/documents/{document['id']}",
        headers={"Authorization": f"Bearer {token}"},
        json={},
    )

    assert response.status_code == 422


def test_update_document_rejects_protected_fields(
    client: TestClient,
    register_and_login,
    create_workspace,
) -> None:
    _, token = register_and_login(client)
    workspace = create_workspace(client, token, "Project Workspace")
    document = create_document(client, token, workspace["id"], "Original Notes")

    response = client.patch(
        f"/api/v1/workspaces/{workspace['id']}/documents/{document['id']}",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "title": "Updated Notes",
            "owner_id": str(uuid.uuid4()),
        },
    )

    assert response.status_code == 422


def test_update_document_returns_404_for_document_in_another_workspace(
    client: TestClient,
    register_and_login,
    create_workspace,
) -> None:
    _, token = register_and_login(client)
    first_workspace = create_workspace(client, token, "First Workspace")
    second_workspace = create_workspace(client, token, "Second Workspace")
    document = create_document(
        client,
        token,
        first_workspace["id"],
        "First Workspace Notes",
    )

    response = client.patch(
        f"/api/v1/workspaces/{second_workspace['id']}/documents/{document['id']}",
        headers={"Authorization": f"Bearer {token}"},
        json={"title": "Updated Notes"},
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "Document not found"}


def test_delete_document_deletes_document_for_workspace_owner(
    client: TestClient,
    register_and_login,
    create_workspace,
) -> None:
    _, token = register_and_login(client)
    workspace = create_workspace(client, token, "Project Workspace")
    document = create_document(client, token, workspace["id"], "Notes To Delete")

    delete_response = client.delete(
        f"/api/v1/workspaces/{workspace['id']}/documents/{document['id']}",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert delete_response.status_code == 204
    assert delete_response.content == b""

    get_response = client.get(
        f"/api/v1/workspaces/{workspace['id']}/documents/{document['id']}",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert get_response.status_code == 404
    assert get_response.json() == {"detail": "Document not found"}


def test_delete_document_requires_authentication(client: TestClient) -> None:
    response = client.delete(
        f"/api/v1/workspaces/{uuid.uuid4()}/documents/{uuid.uuid4()}"
    )

    assert response.status_code == 401
    assert response.json() == {"detail": "Not authenticated"}


def test_delete_document_returns_404_for_missing_workspace(
    client: TestClient,
    register_and_login,
) -> None:
    _, token = register_and_login(client)

    response = client.delete(
        f"/api/v1/workspaces/{uuid.uuid4()}/documents/{uuid.uuid4()}",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "Workspace not found"}


def test_delete_document_returns_404_for_missing_document(
    client: TestClient,
    register_and_login,
    create_workspace,
) -> None:
    _, token = register_and_login(client)
    workspace = create_workspace(client, token, "Project Workspace")

    response = client.delete(
        f"/api/v1/workspaces/{workspace['id']}/documents/{uuid.uuid4()}",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "Document not found"}


def test_delete_document_returns_404_for_another_users_workspace(
    client: TestClient,
    register_and_login,
    create_workspace,
) -> None:
    _, owner_token = register_and_login(client)
    _, other_token = register_and_login(client)

    workspace = create_workspace(client, owner_token, "Private Workspace")
    document = create_document(client, owner_token, workspace["id"], "Private Notes")

    response = client.delete(
        f"/api/v1/workspaces/{workspace['id']}/documents/{document['id']}",
        headers={"Authorization": f"Bearer {other_token}"},
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "Workspace not found"}


def test_delete_document_returns_404_for_document_in_another_workspace(
    client: TestClient,
    register_and_login,
    create_workspace,
) -> None:
    _, token = register_and_login(client)
    first_workspace = create_workspace(client, token, "First Workspace")
    second_workspace = create_workspace(client, token, "Second Workspace")
    document = create_document(
        client,
        token,
        first_workspace["id"],
        "First Workspace Notes",
    )

    response = client.delete(
        f"/api/v1/workspaces/{second_workspace['id']}/documents/{document['id']}",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "Document not found"}
