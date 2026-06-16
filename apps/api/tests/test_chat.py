import uuid

from fastapi.testclient import TestClient

from tests.test_documents import create_document


def test_chat_workspace_requires_authentication(client: TestClient) -> None:
    response = client.post(
        f"/api/v1/workspaces/{uuid.uuid4()}/chat",
        json={
            "question": "What does this workspace contain?",
        },
    )

    assert response.status_code == 401
    assert response.json() == {"detail": "Not authenticated"}


def test_chat_workspace_returns_404_for_missing_workspace(
    client: TestClient,
    register_and_login,
) -> None:
    _, token = register_and_login(client)

    response = client.post(
        f"/api/v1/workspaces/{uuid.uuid4()}/chat",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "question": "What does this workspace contain?",
        },
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "Workspace not found"}


def test_chat_workspace_returns_404_for_another_users_workspace(
    client: TestClient,
    register_and_login,
    create_workspace,
) -> None:
    _, owner_token = register_and_login(client)
    _, other_token = register_and_login(client)
    workspace = create_workspace(client, owner_token, "Private Workspace")

    response = client.post(
        f"/api/v1/workspaces/{workspace['id']}/chat",
        headers={"Authorization": f"Bearer {other_token}"},
        json={
            "question": "What is private?",
        },
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "Workspace not found"}


def test_chat_workspace_returns_answer_and_citations(
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
        content="Raw project evidence for chat answers",
    )

    source_elements_response = client.get(
        f"/api/v1/workspaces/{workspace['id']}/documents/{document['id']}/source-elements",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert source_elements_response.status_code == 200
    source_element = source_elements_response.json()[0]

    response = client.post(
        f"/api/v1/workspaces/{workspace['id']}/chat",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "question": "What evidence is available?",
        },
    )

    assert response.status_code == 200
    data = response.json()

    assert "Raw project evidence for chat answers" in data["answer"]
    assert len(data["citations"]) == 1
    citation = data["citations"][0]
    assert citation["source_element_id"] == source_element["id"]
    assert citation["document_id"] == document["id"]
    assert citation["workspace_id"] == workspace["id"]
    assert citation["snippet"] == "Raw project evidence for chat answers"
