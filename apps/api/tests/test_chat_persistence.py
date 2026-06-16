import uuid
from collections.abc import AsyncGenerator

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.db.session import AsyncSessionLocal, engine
from app.modules.auth.service import create_user
from app.modules.chat.models import ChatMessage, ChatMessageCitation, ChatSession
from app.modules.chat.service import answer_workspace_question
from app.modules.documents.service import create_document
from app.modules.workspaces.service import create_workspace


@pytest.fixture
async def db_session() -> AsyncGenerator[AsyncSession]:
    try:
        async with AsyncSessionLocal() as db:
            yield db
    finally:
        await engine.dispose()


@pytest.mark.anyio
async def test_answer_workspace_question_persists_chat_session_messages_and_citations(
    db_session: AsyncSession,
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        "app.modules.chat.service.get_settings",
        lambda: Settings(
            database_url=(
                "postgresql+asyncpg://placeholder:placeholder"
                "@localhost:5432/placeholder"
            ),
            jwt_secret_key="test-secret",
            llm_api_key=None,
        ),
    )

    user = await create_user(
        db_session,
        email=f"user-{uuid.uuid4()}@example.com",
        password="strongpassword123",
    )
    workspace = await create_workspace(
        db_session,
        owner_id=user.id,
        name="Project Workspace",
        description="Project workspace description",
    )
    document = await create_document(
        db=db_session,
        workspace_id=workspace.id,
        owner_id=user.id,
        title="Project Notes",
        source_type="text",
        content="Raw persisted citation evidence",
    )

    answer, citations = await answer_workspace_question(
        db=db_session,
        workspace_id=workspace.id,
        owner_id=user.id,
        question="What evidence should be persisted?",
        limit=5,
    )

    sessions_result = await db_session.execute(
        select(ChatSession).where(
            ChatSession.workspace_id == workspace.id,
            ChatSession.owner_id == user.id,
        )
    )
    sessions = list(sessions_result.scalars().all())

    assert len(sessions) == 1
    session = sessions[0]
    assert session.title == "What evidence should be persisted?"

    messages_result = await db_session.execute(
        select(ChatMessage)
        .where(ChatMessage.session_id == session.id)
        .order_by(ChatMessage.message_index.asc())
    )
    messages = list(messages_result.scalars().all())

    assert len(messages) == 2
    assert messages[0].role == "user"
    assert messages[0].content == "What evidence should be persisted?"
    assert messages[0].message_index == 0
    assert messages[1].role == "assistant"
    assert messages[1].content == answer
    assert messages[1].message_index == 1

    citations_result = await db_session.execute(
        select(ChatMessageCitation).where(
            ChatMessageCitation.message_id == messages[1].id
        )
    )
    persisted_citations = list(citations_result.scalars().all())

    assert len(persisted_citations) == 1
    assert len(citations) == 1
    assert persisted_citations[0].session_id == session.id
    assert persisted_citations[0].document_id == document.id
    assert persisted_citations[0].source_element_id == citations[0].source_element_id
    assert persisted_citations[0].workspace_id == workspace.id
    assert persisted_citations[0].owner_id == user.id
    assert persisted_citations[0].citation_index == 0
    assert persisted_citations[0].snippet == "Raw persisted citation evidence"
