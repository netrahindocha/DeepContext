import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db_session
from app.modules.auth.dependencies import get_current_user
from app.modules.auth.models import User
from app.modules.documents.schemas import DocumentCreate, DocumentRead, DocumentUpdate
from app.modules.documents.service import (
    create_document,
    delete_document,
    get_document_for_workspace,
    list_documents_for_workspace,
    update_document,
)
from app.modules.workspaces.service import get_workspace_for_owner

router = APIRouter(
    prefix="/api/v1/workspaces/{workspace_id}/documents",
    tags=["documents"],
)


@router.post("", response_model=DocumentRead, status_code=status.HTTP_201_CREATED)
async def create_document_route(
    workspace_id: uuid.UUID,
    payload: DocumentCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> DocumentRead:
    workspace = await get_workspace_for_owner(
        db=db,
        workspace_id=workspace_id,
        owner_id=current_user.id,
    )

    if workspace is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workspace not found",
        )

    document = await create_document(
        db=db,
        workspace_id=workspace.id,
        owner_id=current_user.id,
        title=payload.title,
        source_type=payload.source_type,
    )

    return DocumentRead.model_validate(document)


@router.get("", response_model=list[DocumentRead])
async def list_documents_route(
    workspace_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> list[DocumentRead]:
    workspace = await get_workspace_for_owner(
        db=db,
        workspace_id=workspace_id,
        owner_id=current_user.id,
    )

    if workspace is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workspace not found",
        )

    documents = await list_documents_for_workspace(
        db=db,
        workspace_id=workspace.id,
        owner_id=current_user.id,
    )

    return [DocumentRead.model_validate(document) for document in documents]


@router.get("/{document_id}", response_model=DocumentRead)
async def get_document_route(
    workspace_id: uuid.UUID,
    document_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> DocumentRead:
    workspace = await get_workspace_for_owner(
        db=db,
        workspace_id=workspace_id,
        owner_id=current_user.id,
    )

    if workspace is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workspace not found",
        )

    document = await get_document_for_workspace(
        db=db,
        workspace_id=workspace.id,
        owner_id=current_user.id,
        document_id=document_id,
    )

    if document is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found",
        )

    return DocumentRead.model_validate(document)


@router.patch("/{document_id}", response_model=DocumentRead)
async def update_document_route(
    workspace_id: uuid.UUID,
    document_id: uuid.UUID,
    payload: DocumentUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> DocumentRead:
    workspace = await get_workspace_for_owner(
        db=db,
        workspace_id=workspace_id,
        owner_id=current_user.id,
    )

    if workspace is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Workspace not found"
        )

    document = await get_document_for_workspace(
        db=db,
        workspace_id=workspace.id,
        owner_id=current_user.id,
        document_id=document_id,
    )

    if document is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found",
        )

    updated_document = await update_document(
        db=db,
        document=document,
        title=payload.title,
    )

    return DocumentRead.model_validate(updated_document)


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document_route(
    workspace_id: uuid.UUID,
    document_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> None:
    workspace = await get_workspace_for_owner(
        db=db,
        workspace_id=workspace_id,
        owner_id=current_user.id,
    )

    if workspace is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workspace not found",
        )

    document = await get_document_for_workspace(
        db=db,
        workspace_id=workspace.id,
        owner_id=current_user.id,
        document_id=document_id,
    )

    if document is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found",
        )

    await delete_document(db=db, document=document)
