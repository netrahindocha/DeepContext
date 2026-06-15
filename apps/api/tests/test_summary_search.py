import uuid

from fastapi.testclient import TestClient

from tests.test_documents import create_document


def test_search_workspace_requires_authentication(client: TestClient) -> None:
    response = client.post(
        f"/api/v1/workspaces/{uuid.uuid4()}/search",
        json={
            "query": "project notes",
        },
    )

    assert response.status_code == 401
    assert response.json() == {"detail": "Not authenticated"}


def test_search_workspace_returns_404_for_missing_workspace(
    client: TestClient,
    register_and_login,
) -> None:
    _, token = register_and_login(client)

    response = client.post(
        f"/api/v1/workspaces/{uuid.uuid4()}/search",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "query": "project notes",
        },
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "Workspace not found"}


def test_search_workspace_returns_404_for_another_users_workspace(
    client: TestClient,
    register_and_login,
    create_workspace,
) -> None:
    _, owner_token = register_and_login(client)
    _, other_token = register_and_login(client)
    workspace = create_workspace(client, owner_token, "Private Workspace")

    response = client.post(
        f"/api/v1/workspaces/{workspace['id']}/search",
        headers={"Authorization": f"Bearer {other_token}"},
        json={
            "query": "private notes",
        },
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "Workspace not found"}


def test_search_workspace_returns_summary_results(
    client: TestClient,
    register_and_login,
    create_workspace,
) -> None:
    _, token = register_and_login(client)
    workspace = create_workspace(client, token, "Project Workspace")
    document = create_document(
        client=client,
        token=token,
        workspace_id=workspace["id"],
        title="Project Notes",
        content="Important search context",
    )

    response = client.post(
        f"/api/v1/workspaces/{workspace['id']}/search",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "query": "Important search context",
        },
    )

    assert response.status_code == 200
    data = response.json()

    assert len(data["results"]) == 1
    result = data["results"][0]
    assert result["document_id"] == document["id"]
    assert result["workspace_id"] == workspace["id"]
    assert result["summary_text"] == "Important search context"
    assert result["distance"] >= 0
    assert "source_element_id" in result
    assert "raw_content_text" not in result


def test_search_workspace_does_not_return_results_from_another_workspace(
    client: TestClient,
    register_and_login,
    create_workspace,
) -> None:
    _, token = register_and_login(client)
    first_workspace = create_workspace(client, token, "First Workspace")
    second_workspace = create_workspace(client, token, "Second Workspace")
    first_document = create_document(
        client=client,
        token=token,
        workspace_id=first_workspace["id"],
        title="First Notes",
        content="First workspace search context",
    )
    create_document(
        client=client,
        token=token,
        workspace_id=second_workspace["id"],
        title="Second Notes",
        content="Second workspace search context",
    )

    response = client.post(
        f"/api/v1/workspaces/{first_workspace['id']}/search",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "query": "First workspace search context",
        },
    )

    assert response.status_code == 200
    data = response.json()

    assert len(data["results"]) == 1
    assert data["results"][0]["document_id"] == first_document["id"]
    assert data["results"][0]["workspace_id"] == first_workspace["id"]


def test_search_workspace_does_not_return_results_from_another_user(
    client: TestClient,
    register_and_login,
    create_workspace,
) -> None:
    _, first_token = register_and_login(client)
    _, second_token = register_and_login(client)

    first_workspace = create_workspace(client, first_token, "First User Workspace")
    second_workspace = create_workspace(client, second_token, "Second User Workspace")
    first_document = create_document(
        client=client,
        token=first_token,
        workspace_id=first_workspace["id"],
        title="First User Notes",
        content="First user search context",
    )
    create_document(
        client=client,
        token=second_token,
        workspace_id=second_workspace["id"],
        title="Second User Notes",
        content="Second user search context",
    )

    response = client.post(
        f"/api/v1/workspaces/{first_workspace['id']}/search",
        headers={"Authorization": f"Bearer {first_token}"},
        json={
            "query": "First user search context",
        },
    )

    assert response.status_code == 200
    data = response.json()

    assert len(data["results"]) == 1
    assert data["results"][0]["document_id"] == first_document["id"]
    assert data["results"][0]["workspace_id"] == first_workspace["id"]


def test_search_workspace_rejects_empty_query(
    client: TestClient,
    register_and_login,
    create_workspace,
) -> None:
    _, token = register_and_login(client)
    workspace = create_workspace(client, token, "Project Workspace")

    response = client.post(
        f"/api/v1/workspaces/{workspace['id']}/search",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "query": "",
        },
    )

    assert response.status_code == 422


def test_search_workspace_rejects_limit_above_maximum(
    client: TestClient,
    register_and_login,
    create_workspace,
) -> None:
    _, token = register_and_login(client)
    workspace = create_workspace(client, token, "Project Workspace")

    response = client.post(
        f"/api/v1/workspaces/{workspace['id']}/search",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "query": "project notes",
            "limit": 21,
        },
    )

    assert response.status_code == 422
