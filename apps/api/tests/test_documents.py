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


def test_create_document_rejects_content_that_is_too_large(
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
            "content": "a" * 100_001,
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


def test_list_source_elements_returns_created_element_for_workspace_owner(
    client: TestClient,
    register_and_login,
    create_workspace,
) -> None:
    _, token = register_and_login(client)
    workspace = create_workspace(client, token, "Project Workspace")
    document = create_document(
        client,
        token,
        workspace["id"],
        "Project Notes",
        content="Raw source evidence",
    )

    response = client.get(
        f"/api/v1/workspaces/{workspace['id']}/documents/{document['id']}/source-elements",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    data = response.json()

    assert len(data) == 1
    assert data[0]["document_id"] == document["id"]
    assert data[0]["workspace_id"] == workspace["id"]
    assert data[0]["owner_id"] == workspace["owner_id"]
    assert data[0]["element_index"] == 0
    assert data[0]["modality"] == "text"
    assert data[0]["status"] == "completed"
    assert data[0]["error_message"] is None
    assert "raw_content_text" not in data[0]
    assert "id" in data[0]
    assert "created_at" in data[0]


def test_list_source_elements_requires_authentication(client: TestClient) -> None:
    workspace_id = uuid.uuid4()
    document_id = uuid.uuid4()

    response = client.get(
        f"/api/v1/workspaces/{workspace_id}/documents/{document_id}/source-elements"
    )

    assert response.status_code == 401
    assert response.json() == {"detail": "Not authenticated"}


def test_list_source_elements_returns_404_for_missing_workspace(
    client: TestClient,
    register_and_login,
) -> None:
    _, token = register_and_login(client)

    response = client.get(
        f"/api/v1/workspaces/{uuid.uuid4()}/documents/{uuid.uuid4()}/source-elements",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "Workspace not found"}


def test_list_source_elements_returns_404_for_another_users_workspace(
    client: TestClient,
    register_and_login,
    create_workspace,
) -> None:
    _, owner_token = register_and_login(client)
    _, other_token = register_and_login(client)

    workspace = create_workspace(client, owner_token, "Private Workspace")
    document = create_document(client, owner_token, workspace["id"], "Private Notes")

    response = client.get(
        f"/api/v1/workspaces/{workspace['id']}/documents/{document['id']}/source-elements",
        headers={"Authorization": f"Bearer {other_token}"},
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "Workspace not found"}


def test_list_source_elements_returns_404_for_missing_document(
    client: TestClient,
    register_and_login,
    create_workspace,
) -> None:
    _, token = register_and_login(client)
    workspace = create_workspace(client, token, "Project Workspace")

    response = client.get(
        f"/api/v1/workspaces/{workspace['id']}/documents/{uuid.uuid4()}/source-elements",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "Document not found"}


def test_list_source_elements_returns_404_for_document_in_another_workspace(
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
        f"/api/v1/workspaces/{second_workspace['id']}/documents/{document['id']}/source-elements",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "Document not found"}


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


def test_get_source_element_returns_element_for_workspace_owner(
    client: TestClient,
    register_and_login,
    create_workspace,
) -> None:
    _, token = register_and_login(client)
    workspace = create_workspace(client, token, "Project Workspace")
    document = create_document(
        client,
        token,
        workspace["id"],
        "Project Notes",
        content="Raw source evidence",
    )

    list_response = client.get(
        f"/api/v1/workspaces/{workspace['id']}/documents/{document['id']}/source-elements",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert list_response.status_code == 200
    source_element = list_response.json()[0]

    response = client.get(
        f"/api/v1/workspaces/{workspace['id']}/documents/{document['id']}/source-elements/{source_element['id']}",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    data = response.json()

    assert data["id"] == source_element["id"]
    assert data["document_id"] == document["id"]
    assert data["workspace_id"] == workspace["id"]
    assert data["owner_id"] == workspace["owner_id"]
    assert data["element_index"] == 0
    assert data["modality"] == "text"
    assert data["raw_content_text"] == "Raw source evidence"
    assert data["status"] == "completed"
    assert data["error_message"] is None


def test_get_source_element_requires_authentication(client: TestClient) -> None:
    response = client.get(
        f"/api/v1/workspaces/{uuid.uuid4()}/documents/{uuid.uuid4()}/source-elements/{uuid.uuid4()}"
    )

    assert response.status_code == 401
    assert response.json() == {"detail": "Not authenticated"}


def test_get_source_element_returns_404_for_missing_workspace(
    client: TestClient,
    register_and_login,
) -> None:
    _, token = register_and_login(client)

    response = client.get(
        f"/api/v1/workspaces/{uuid.uuid4()}/documents/{uuid.uuid4()}/source-elements/{uuid.uuid4()}",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "Workspace not found"}


def test_get_source_element_returns_404_for_another_users_workspace(
    client: TestClient,
    register_and_login,
    create_workspace,
) -> None:
    _, owner_token = register_and_login(client)
    _, other_token = register_and_login(client)

    workspace = create_workspace(client, owner_token, "Private Workspace")
    document = create_document(client, owner_token, workspace["id"], "Private Notes")

    list_response = client.get(
        f"/api/v1/workspaces/{workspace['id']}/documents/{document['id']}/source-elements",
        headers={"Authorization": f"Bearer {owner_token}"},
    )
    assert list_response.status_code == 200
    source_element = list_response.json()[0]

    response = client.get(
        f"/api/v1/workspaces/{workspace['id']}/documents/{document['id']}/source-elements/{source_element['id']}",
        headers={"Authorization": f"Bearer {other_token}"},
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "Workspace not found"}


def test_get_source_element_returns_404_for_missing_document(
    client: TestClient,
    register_and_login,
    create_workspace,
) -> None:
    _, token = register_and_login(client)
    workspace = create_workspace(client, token, "Project Workspace")

    response = client.get(
        f"/api/v1/workspaces/{workspace['id']}/documents/{uuid.uuid4()}/source-elements/{uuid.uuid4()}",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "Document not found"}


def test_get_source_element_returns_404_for_source_element_in_another_document(
    client: TestClient,
    register_and_login,
    create_workspace,
) -> None:
    _, token = register_and_login(client)
    workspace = create_workspace(client, token, "Project Workspace")
    first_document = create_document(client, token, workspace["id"], "First Notes")
    second_document = create_document(client, token, workspace["id"], "Second Notes")

    list_response = client.get(
        f"/api/v1/workspaces/{workspace['id']}/documents/{first_document['id']}/source-elements",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert list_response.status_code == 200
    source_element = list_response.json()[0]

    response = client.get(
        f"/api/v1/workspaces/{workspace['id']}/documents/{second_document['id']}/source-elements/{source_element['id']}",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "Source element not found"}


def test_get_source_element_returns_404_for_document_in_another_workspace(
    client: TestClient,
    register_and_login,
    create_workspace,
) -> None:
    _, token = register_and_login(client)
    first_workspace = create_workspace(client, token, "First Workspace")
    second_workspace = create_workspace(client, token, "Second Workspace")
    document = create_document(client, token, first_workspace["id"], "First Notes")

    list_response = client.get(
        f"/api/v1/workspaces/{first_workspace['id']}/documents/{document['id']}/source-elements",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert list_response.status_code == 200
    source_element = list_response.json()[0]

    response = client.get(
        f"/api/v1/workspaces/{second_workspace['id']}/documents/{document['id']}/source-elements/{source_element['id']}",
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
