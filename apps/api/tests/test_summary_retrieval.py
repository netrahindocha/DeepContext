import uuid
from collections.abc import AsyncGenerator

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import AsyncSessionLocal, engine
from app.modules.auth.service import create_user
from app.modules.documents.service import (
    create_document,
    create_placeholder_embedding,
    get_source_elements_for_summaries,
    search_source_element_summaries,
)
from app.modules.workspaces.service import create_workspace


@pytest.fixture
async def db_session() -> AsyncGenerator[AsyncSession]:
    try:
        async with AsyncSessionLocal() as db:
            yield db
    finally:
        await engine.dispose()


@pytest.mark.anyio
async def test_create_document_creates_summary_with_embedding(
    db_session: AsyncSession,
) -> None:
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
        content="Important project context",
    )

    results = await search_source_element_summaries(
        db=db_session,
        workspace_id=workspace.id,
        owner_id=user.id,
        query_embedding=create_placeholder_embedding("Important project context"),
        limit=5,
    )

    assert len(results) == 1
    assert results[0].summary.document_id == document.id
    assert results[0].summary.workspace_id == workspace.id
    assert results[0].summary.owner_id == user.id
    assert results[0].summary.summary_text == "Important project context"
    assert results[0].summary.embedding is not None
    assert results[0].source_element_id == results[0].summary.source_element_id
    assert results[0].document_id == document.id
    assert results[0].workspace_id == workspace.id
    assert results[0].owner_id == user.id
    assert results[0].distance >= 0


@pytest.mark.anyio
async def test_search_source_element_summaries_scopes_by_workspace(
    db_session: AsyncSession,
) -> None:
    user = await create_user(
        db_session,
        email=f"user-{uuid.uuid4()}@example.com",
        password="strongpassword123",
    )
    first_workspace = await create_workspace(
        db_session,
        owner_id=user.id,
        name="First Workspace",
        description="First workspace description",
    )
    second_workspace = await create_workspace(
        db_session,
        owner_id=user.id,
        name="Second Workspace",
        description="Second workspace description",
    )

    first_document = await create_document(
        db=db_session,
        workspace_id=first_workspace.id,
        owner_id=user.id,
        title="First Notes",
        source_type="text",
        content="First workspace context",
    )
    await create_document(
        db=db_session,
        workspace_id=second_workspace.id,
        owner_id=user.id,
        title="Second Notes",
        source_type="text",
        content="Second workspace context",
    )

    results = await search_source_element_summaries(
        db=db_session,
        workspace_id=first_workspace.id,
        owner_id=user.id,
        query_embedding=create_placeholder_embedding("First workspace context"),
        limit=5,
    )

    assert len(results) == 1
    assert results[0].summary.document_id == first_document.id
    assert results[0].summary.workspace_id == first_workspace.id
    assert results[0].document_id == first_document.id
    assert results[0].workspace_id == first_workspace.id
    assert results[0].owner_id == user.id
    assert results[0].distance >= 0


@pytest.mark.anyio
async def test_search_source_element_summaries_scopes_by_owner(
    db_session: AsyncSession,
) -> None:
    first_user = await create_user(
        db_session,
        email=f"user-{uuid.uuid4()}@example.com",
        password="strongpassword123",
    )
    second_user = await create_user(
        db_session,
        email=f"user-{uuid.uuid4()}@example.com",
        password="strongpassword123",
    )
    workspace = await create_workspace(
        db_session,
        owner_id=first_user.id,
        name="Shared Workspace Id Scope",
        description="Workspace description",
    )

    first_document = await create_document(
        db=db_session,
        workspace_id=workspace.id,
        owner_id=first_user.id,
        title="First User Notes",
        source_type="text",
        content="First user context",
    )
    await create_document(
        db=db_session,
        workspace_id=workspace.id,
        owner_id=second_user.id,
        title="Second User Notes",
        source_type="text",
        content="Second user context",
    )

    results = await search_source_element_summaries(
        db=db_session,
        workspace_id=workspace.id,
        owner_id=first_user.id,
        query_embedding=create_placeholder_embedding("First user context"),
        limit=5,
    )

    assert len(results) == 1
    assert results[0].summary.document_id == first_document.id
    assert results[0].summary.owner_id == first_user.id
    assert results[0].document_id == first_document.id
    assert results[0].workspace_id == workspace.id
    assert results[0].owner_id == first_user.id
    assert results[0].distance >= 0


@pytest.mark.anyio
async def test_get_source_elements_for_summaries_returns_raw_evidence(
    db_session: AsyncSession,
) -> None:
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

    await create_document(
        db=db_session,
        workspace_id=workspace.id,
        owner_id=user.id,
        title="Project Notes",
        source_type="text",
        content="Raw evidence for answer generation",
    )

    summary_results = await search_source_element_summaries(
        db=db_session,
        workspace_id=workspace.id,
        owner_id=user.id,
        query_embedding=create_placeholder_embedding(
            "Raw evidence for answer generation"
        ),
        limit=5,
    )

    source_elements = await get_source_elements_for_summaries(
        db=db_session,
        workspace_id=workspace.id,
        owner_id=user.id,
        summary_results=summary_results,
    )

    assert len(source_elements) == 1
    assert source_elements[0].workspace_id == workspace.id
    assert source_elements[0].owner_id == user.id
    assert source_elements[0].raw_content_text == "Raw evidence for answer generation"


@pytest.mark.anyio
async def test_get_source_elements_for_summaries_returns_empty_list_for_no_results(
    db_session: AsyncSession,
) -> None:
    source_elements = await get_source_elements_for_summaries(
        db=db_session,
        workspace_id=uuid.uuid4(),
        owner_id=uuid.uuid4(),
        summary_results=[],
    )

    assert source_elements == []
