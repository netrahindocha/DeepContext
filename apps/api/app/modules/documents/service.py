import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.documents.models import Document, SourceElement


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
