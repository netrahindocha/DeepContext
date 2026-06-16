import uuid

from fastapi.testclient import TestClient

from tests.test_documents import create_document


def create_chat_session(
    client: TestClient,
    token: str,
    workspace_id: str,
    question: str,
) -> dict:
    chat_response = client.post(
        f"/api/v1/workspaces/{workspace_id}/chat",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "question": question,
        },
    )
    assert chat_response.status_code == 200

    sessions_response = client.get(
        f"/api/v1/workspaces/{workspace_id}/chat/sessions",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert sessions_response.status_code == 200

    return sessions_response.json()[0]


def test_list_chat_sessions_requires_authentication(client: TestClient) -> None:
    response = client.get(f"/api/v1/workspaces/{uuid.uuid4()}/chat/sessions")

    assert response.status_code == 401
    assert response.json() == {"detail": "Not authenticated"}


def test_list_chat_sessions_returns_workspace_sessions(
    client: TestClient,
    register_and_login,
    create_workspace,
) -> None:
    _, token = register_and_login(client)
    workspace = create_workspace(client, token, "Project Workspace")
    create_document(
        client=client,
        token=token,
        workspace_id=workspace["id"],
        title="Project Notes",
        content="Raw chat history evidence",
    )

    chat_response = client.post(
        f"/api/v1/workspaces/{workspace['id']}/chat",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "question": "What should be stored?",
        },
    )
    assert chat_response.status_code == 200

    response = client.get(
        f"/api/v1/workspaces/{workspace['id']}/chat/sessions",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    sessions = response.json()

    assert len(sessions) == 1
    assert sessions[0]["workspace_id"] == workspace["id"]
    assert sessions[0]["owner_id"] == workspace["owner_id"]
    assert sessions[0]["title"] == "What should be stored?"
    assert "id" in sessions[0]
    assert "created_at" in sessions[0]
    assert "updated_at" in sessions[0]


def test_list_chat_messages_returns_messages_and_citations(
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
        content="Raw chat message citation evidence",
    )

    chat_response = client.post(
        f"/api/v1/workspaces/{workspace['id']}/chat",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "question": "What evidence is stored?",
        },
    )
    assert chat_response.status_code == 200

    sessions_response = client.get(
        f"/api/v1/workspaces/{workspace['id']}/chat/sessions",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert sessions_response.status_code == 200
    session = sessions_response.json()[0]

    response = client.get(
        f"/api/v1/workspaces/{workspace['id']}/chat/sessions/{session['id']}/messages",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    messages = response.json()

    assert len(messages) == 2

    assert messages[0]["role"] == "user"
    assert messages[0]["content"] == "What evidence is stored?"
    assert messages[0]["message_index"] == 0
    assert messages[0]["citations"] == []

    assert messages[1]["role"] == "assistant"
    assert "Raw chat message citation evidence" in messages[1]["content"]
    assert messages[1]["message_index"] == 1
    assert len(messages[1]["citations"]) == 1

    citation = messages[1]["citations"][0]
    assert citation["document_id"] == document["id"]
    assert citation["workspace_id"] == workspace["id"]
    assert citation["citation_index"] == 0
    assert citation["snippet"] == "Raw chat message citation evidence"


def test_list_chat_messages_returns_404_for_missing_session(
    client: TestClient,
    register_and_login,
    create_workspace,
) -> None:
    _, token = register_and_login(client)
    workspace = create_workspace(client, token, "Project Workspace")

    response = client.get(
        f"/api/v1/workspaces/{workspace['id']}/chat/sessions/{uuid.uuid4()}/messages",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "Chat session not found"}


def test_list_chat_messages_requires_authentication(client: TestClient) -> None:
    response = client.get(
        f"/api/v1/workspaces/{uuid.uuid4()}/chat/sessions/{uuid.uuid4()}/messages"
    )

    assert response.status_code == 401
    assert response.json() == {"detail": "Not authenticated"}


def test_list_chat_sessions_returns_404_for_another_users_workspace(
    client: TestClient,
    register_and_login,
    create_workspace,
) -> None:
    _, owner_token = register_and_login(client)
    _, other_token = register_and_login(client)

    workspace = create_workspace(client, owner_token, "Private Workspace")
    create_document(
        client=client,
        token=owner_token,
        workspace_id=workspace["id"],
        title="Private Notes",
        content="Private chat evidence",
    )
    create_chat_session(
        client=client,
        token=owner_token,
        workspace_id=workspace["id"],
        question="What is private?",
    )

    response = client.get(
        f"/api/v1/workspaces/{workspace['id']}/chat/sessions",
        headers={"Authorization": f"Bearer {other_token}"},
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "Workspace not found"}


def test_list_chat_messages_returns_404_for_another_users_workspace(
    client: TestClient,
    register_and_login,
    create_workspace,
) -> None:
    _, owner_token = register_and_login(client)
    _, other_token = register_and_login(client)

    workspace = create_workspace(client, owner_token, "Private Workspace")
    create_document(
        client=client,
        token=owner_token,
        workspace_id=workspace["id"],
        title="Private Notes",
        content="Private message evidence",
    )
    session = create_chat_session(
        client=client,
        token=owner_token,
        workspace_id=workspace["id"],
        question="What is private?",
    )

    response = client.get(
        f"/api/v1/workspaces/{workspace['id']}/chat/sessions/{session['id']}/messages",
        headers={"Authorization": f"Bearer {other_token}"},
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "Workspace not found"}


def test_list_chat_messages_returns_404_for_session_in_another_workspace(
    client: TestClient,
    register_and_login,
    create_workspace,
) -> None:
    _, token = register_and_login(client)

    first_workspace = create_workspace(client, token, "First Workspace")
    second_workspace = create_workspace(client, token, "Second Workspace")

    create_document(
        client=client,
        token=token,
        workspace_id=first_workspace["id"],
        title="First Notes",
        content="First workspace chat evidence",
    )
    session = create_chat_session(
        client=client,
        token=token,
        workspace_id=first_workspace["id"],
        question="What is in the first workspace?",
    )

    response = client.get(
        f"/api/v1/workspaces/{second_workspace['id']}/chat/sessions/{session['id']}/messages",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "Chat session not found"}


def test_list_chat_sessions_only_returns_sessions_for_requested_workspace(
    client: TestClient,
    register_and_login,
    create_workspace,
) -> None:
    _, token = register_and_login(client)

    first_workspace = create_workspace(client, token, "First Workspace")
    second_workspace = create_workspace(client, token, "Second Workspace")

    create_document(
        client=client,
        token=token,
        workspace_id=first_workspace["id"],
        title="First Notes",
        content="First workspace chat evidence",
    )
    create_document(
        client=client,
        token=token,
        workspace_id=second_workspace["id"],
        title="Second Notes",
        content="Second workspace chat evidence",
    )

    first_session = create_chat_session(
        client=client,
        token=token,
        workspace_id=first_workspace["id"],
        question="What is in the first workspace?",
    )
    second_session = create_chat_session(
        client=client,
        token=token,
        workspace_id=second_workspace["id"],
        question="What is in the second workspace?",
    )

    response = client.get(
        f"/api/v1/workspaces/{first_workspace['id']}/chat/sessions",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    sessions = response.json()

    assert len(sessions) == 1
    assert sessions[0]["id"] == first_session["id"]
    assert sessions[0]["id"] != second_session["id"]
    assert sessions[0]["workspace_id"] == first_workspace["id"]
