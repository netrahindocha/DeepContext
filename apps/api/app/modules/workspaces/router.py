import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db_session
from app.modules.auth.dependencies import get_current_user
from app.modules.auth.models import User
from app.modules.workspaces.schemas import (
    WorkspaceCreate,
    WorkspaceRead,
    WorkspaceUpdate,
)
from app.modules.documents.schemas import (
    WorkspaceSearchRequest,
    WorkspaceSearchResponse,
    WorkspaceSearchResult,
)
from app.modules.workspaces.service import (
    create_workspace,
    delete_workspace,
    get_workspace_for_owner,
    list_workspaces_for_owner,
    update_workspace,
)
from app.modules.documents.service import (
    create_placeholder_embedding,
    search_source_element_summaries,
)

router = APIRouter(prefix="/api/v1/workspaces", tags=["workspaces"])


@router.post("", response_model=WorkspaceRead, status_code=status.HTTP_201_CREATED)
async def create_workspace_route(
    payload: WorkspaceCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> WorkspaceRead:
    workspace = await create_workspace(
        db=db,
        owner_id=current_user.id,
        name=payload.name,
        description=payload.description,
    )
    return WorkspaceRead.model_validate(workspace)


@router.get("", response_model=list[WorkspaceRead])
async def list_workspaces_route(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> list[WorkspaceRead]:
    workspaces = await list_workspaces_for_owner(db=db, owner_id=current_user.id)
    return [WorkspaceRead.model_validate(workspace) for workspace in workspaces]


@router.get("/{workspace_id}", response_model=WorkspaceRead)
async def get_workspace_route(
    workspace_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> WorkspaceRead:
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

    return WorkspaceRead.model_validate(workspace)


@router.post("/{workspace_id}/search", response_model=WorkspaceSearchResponse)
async def search_workspace_route(
    workspace_id: uuid.UUID,
    payload: WorkspaceSearchRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> WorkspaceSearchResponse:
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

    query_embedding = create_placeholder_embedding(payload.query)
    results = await search_source_element_summaries(
        db=db,
        workspace_id=workspace.id,
        owner_id=current_user.id,
        query_embedding=query_embedding,
        limit=payload.limit,
    )

    return WorkspaceSearchResponse(
        results=[
            WorkspaceSearchResult(
                source_element_id=result.source_element_id,
                document_id=result.document_id,
                workspace_id=result.workspace_id,
                summary_text=result.summary.summary_text,
                distance=result.distance,
            )
            for result in results
        ]
    )


@router.patch("/{workspace_id}", response_model=WorkspaceRead)
async def update_workspace_route(
    workspace_id: uuid.UUID,
    payload: WorkspaceUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> WorkspaceRead:
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

    updated_workspace = await update_workspace(
        db=db,
        workspace=workspace,
        name=payload.name,
        description=payload.description,
    )

    return WorkspaceRead.model_validate(updated_workspace)


@router.delete("/{workspace_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_workspace_route(
    workspace_id: uuid.UUID,
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
            status_code=status.HTTP_404_NOT_FOUND, detail="Workspace not found"
        )

    await delete_workspace(db=db, workspace=workspace)
