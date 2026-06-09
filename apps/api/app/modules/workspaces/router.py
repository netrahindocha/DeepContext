from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db_session
from app.modules.auth.dependencies import get_current_user
from app.modules.auth.models import User
from app.modules.workspaces.schemas import WorkspaceCreate, WorkspaceRead
from app.modules.workspaces.service import create_workspace, list_workspaces_for_owner

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
