import uuid

from fastapi.testclient import TestClient

from tests.test_documents import create_document

from app.modules.chat.service import AnswerEvidence, generate_answer_from_evidence


def test_generate_answer_from_evidence_returns_fallback_without_evidence() -> None:
    answer = generate_answer_from_evidence(
        question="What is available?",
        evidence=[],
    )

    assert answer == "I could not find relevant source content for that question."


def test_generate_answer_from_evidence_uses_raw_evidence_text() -> None:
    evidence = [
        AnswerEvidence(
            source_element_id=uuid.uuid4(),
            document_id=uuid.uuid4(),
            workspace_id=uuid.uuid4(),
            raw_content_text="Raw source evidence for answer generation",
        )
    ]

    answer = generate_answer_from_evidence(
        question="What is available?",
        evidence=evidence,
    )

    assert "Raw source evidence for answer generation" in answer


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


def test_chat_workspace_returns_empty_answer_when_no_sources(
    client: TestClient,
    register_and_login,
    create_workspace,
) -> None:
    _, token = register_and_login(client)
    workspace = create_workspace(client, token, "Empty Workspace")

    response = client.post(
        f"/api/v1/workspaces/{workspace['id']}/chat",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "question": "What evidence is available?",
        },
    )

    assert response.status_code == 200
    data = response.json()

    assert (
        data["answer"] == "I could not find relevant source content for that question."
    )
    assert data["citations"] == []


def test_chat_workspace_does_not_use_sources_from_another_workspace(
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
        content="First workspace raw evidence",
    )
    create_document(
        client=client,
        token=token,
        workspace_id=second_workspace["id"],
        title="Second Notes",
        content="Second workspace raw evidence",
    )

    response = client.post(
        f"/api/v1/workspaces/{first_workspace['id']}/chat",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "question": "What evidence exists?",
        },
    )

    assert response.status_code == 200
    data = response.json()

    assert "First workspace raw evidence" in data["answer"]
    assert "Second workspace raw evidence" not in data["answer"]
    assert len(data["citations"]) == 1
    assert data["citations"][0]["document_id"] == first_document["id"]


def test_chat_workspace_does_not_use_sources_from_another_user(
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
        content="First user raw evidence",
    )
    create_document(
        client=client,
        token=second_token,
        workspace_id=second_workspace["id"],
        title="Second User Notes",
        content="Second user raw evidence",
    )

    response = client.post(
        f"/api/v1/workspaces/{first_workspace['id']}/chat",
        headers={"Authorization": f"Bearer {first_token}"},
        json={
            "question": "What evidence exists?",
        },
    )

    assert response.status_code == 200
    data = response.json()

    assert "First user raw evidence" in data["answer"]
    assert "Second user raw evidence" not in data["answer"]
    assert len(data["citations"]) == 1
    assert data["citations"][0]["document_id"] == first_document["id"]


def test_chat_workspace_rejects_empty_question(
    client: TestClient,
    register_and_login,
    create_workspace,
) -> None:
    _, token = register_and_login(client)
    workspace = create_workspace(client, token, "Project Workspace")

    response = client.post(
        f"/api/v1/workspaces/{workspace['id']}/chat",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "question": "",
        },
    )

    assert response.status_code == 422


def test_chat_workspace_rejects_limit_above_maximum(
    client: TestClient,
    register_and_login,
    create_workspace,
) -> None:
    _, token = register_and_login(client)
    workspace = create_workspace(client, token, "Project Workspace")

    response = client.post(
        f"/api/v1/workspaces/{workspace['id']}/chat",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "question": "What evidence exists?",
            "limit": 21,
        },
    )

    assert response.status_code == 422
