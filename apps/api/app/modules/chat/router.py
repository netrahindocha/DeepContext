import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db_session
from app.modules.auth.dependencies import get_current_user
from app.modules.auth.models import User
from app.modules.chat.schemas import ChatRequest, ChatResponse
from app.modules.chat.service import answer_workspace_question
from app.modules.workspaces.service import get_workspace_for_owner

router = APIRouter(
    prefix="/api/v1/workspaces/{workspace_id}/chat",
    tags=["chat"],
)


@router.post("", response_model=ChatResponse)
async def chat_workspace_route(
    workspace_id: uuid.UUID,
    payload: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> ChatResponse:
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

    answer, citations = await answer_workspace_question(
        db=db,
        workspace_id=workspace.id,
        owner_id=current_user.id,
        question=payload.question,
        limit=payload.limit,
    )

    return ChatResponse(answer=answer, citations=citations)
