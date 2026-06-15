import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.documents.models import (
    Document,
    SourceElement,
    SourceElementSummary,
)


EMBEDDING_DIMENSION = 1536


def create_placeholder_embedding(text: str) -> list[float]:
    embedding = [0.0] * EMBEDDING_DIMENSION

    for index, character in enumerate(text[:EMBEDDING_DIMENSION]):
        embedding[index] = (ord(character) % 100) / 100

    return embedding


async def create_document(
    db: AsyncSession,
    workspace_id: uuid.UUID,
    owner_id: uuid.UUID,
    title: str,
    source_type: str,
    content: str,
) -> Document:
    document = Document(
        workspace_id=workspace_id,
        owner_id=owner_id,
        title=title,
        source_type=source_type,
        status="completed",
    )
    db.add(document)
    await db.flush()

    source_element = SourceElement(
        document_id=document.id,
        workspace_id=workspace_id,
        owner_id=owner_id,
        element_index=0,
        modality="text",
        raw_content_text=content,
        status="completed",
    )
    db.add(source_element)
    await db.flush()

    summary_text = content[:500]

    summary = SourceElementSummary(
        source_element_id=source_element.id,
        document_id=document.id,
        workspace_id=workspace_id,
        owner_id=owner_id,
        summary_text=summary_text,
        embedding=create_placeholder_embedding(summary_text),
        status="completed",
    )
    db.add(summary)

    await db.commit()
    await db.refresh(document)

    return document


async def list_documents_for_workspace(
    db: AsyncSession,
    workspace_id: uuid.UUID,
    owner_id: uuid.UUID,
) -> list[Document]:
    result = await db.execute(
        select(Document)
        .where(
            Document.workspace_id == workspace_id,
            Document.owner_id == owner_id,
        )
        .order_by(Document.created_at.desc())
    )
    return list(result.scalars().all())


async def get_document_for_workspace(
    db: AsyncSession,
    workspace_id: uuid.UUID,
    owner_id: uuid.UUID,
    document_id: uuid.UUID,
) -> Document | None:
    result = await db.execute(
        select(Document).where(
            Document.id == document_id,
            Document.workspace_id == workspace_id,
            Document.owner_id == owner_id,
        )
    )
    return result.scalar_one_or_none()


async def update_document(
    db: AsyncSession,
    document: Document,
    title: str,
) -> Document:
    document.title = title

    await db.commit()
    await db.refresh(document)

    return document


async def delete_document(
    db: AsyncSession,
    document: Document,
) -> None:
    await db.delete(document)
    await db.commit()


async def list_source_elements_for_document(
    db: AsyncSession,
    workspace_id: uuid.UUID,
    owner_id: uuid.UUID,
    document_id: uuid.UUID,
) -> list[SourceElement]:
    result = await db.execute(
        select(SourceElement)
        .where(
            SourceElement.document_id == document_id,
            SourceElement.workspace_id == workspace_id,
            SourceElement.owner_id == owner_id,
        )
        .order_by(SourceElement.element_index.asc())
    )
    return list(result.scalars().all())


async def get_source_element_for_document(
    db: AsyncSession,
    workspace_id: uuid.UUID,
    owner_id: uuid.UUID,
    document_id: uuid.UUID,
    source_element_id: uuid.UUID,
) -> SourceElement | None:
    result = await db.execute(
        select(SourceElement).where(
            SourceElement.id == source_element_id,
            SourceElement.document_id == document_id,
            SourceElement.workspace_id == workspace_id,
            SourceElement.owner_id == owner_id,
        )
    )
    return result.scalar_one_or_none()


async def search_source_element_summaries(
    db: AsyncSession,
    workspace_id: uuid.UUID,
    owner_id: uuid.UUID,
    query_embedding: list[float],
    limit: int = 5,
) -> list[SourceElementSummary]:
    result = await db.execute(
        select(SourceElementSummary)
        .where(
            SourceElementSummary.workspace_id == workspace_id,
            SourceElementSummary.owner_id == owner_id,
            SourceElementSummary.embedding.is_not(None),
        )
        .order_by(SourceElementSummary.embedding.l2_distance(query_embedding))
        .limit(limit)
    )
    return list(result.scalars().all())
