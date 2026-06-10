import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.documents.models import Document


async def create_document(
    db: AsyncSession,
    workspace_id: uuid.UUID,
    owner_id: uuid.UUID,
    title: str,
    source_type: str,
) -> Document:
    document = Document(
        workspace_id=workspace_id,
        owner_id=owner_id,
        title=title,
        source_type=source_type,
        status="pending",
    )

    db.add(document)
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
