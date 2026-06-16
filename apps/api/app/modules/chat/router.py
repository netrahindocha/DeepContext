import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db_session
from app.modules.auth.dependencies import get_current_user
from app.modules.auth.models import User
from app.modules.chat.schemas import (
    ChatMessageCitationRead,
    ChatMessageRead,
    ChatRequest,
    ChatResponse,
    ChatSessionRead,
)
from app.modules.chat.service import (
    answer_workspace_question,
    get_chat_session_for_workspace,
    list_chat_messages_with_citations,
    list_chat_sessions_for_workspace,
)
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


@router.get("/sessions", response_model=list[ChatSessionRead])
async def list_chat_sessions_route(
    workspace_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> list[ChatSessionRead]:
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

    sessions = await list_chat_sessions_for_workspace(
        db=db,
        workspace_id=workspace.id,
        owner_id=current_user.id,
    )

    return [ChatSessionRead.model_validate(session) for session in sessions]


@router.get("/sessions/{session_id}/messages", response_model=list[ChatMessageRead])
async def list_chat_messages_route(
    workspace_id: uuid.UUID,
    session_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> list[ChatMessageRead]:
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

    session = await get_chat_session_for_workspace(
        db=db,
        workspace_id=workspace.id,
        owner_id=current_user.id,
        session_id=session_id,
    )

    if session is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat session not found",
        )

    messages_with_citations = await list_chat_messages_with_citations(
        db=db,
        workspace_id=workspace.id,
        owner_id=current_user.id,
        session_id=session.id,
    )

    return [
        ChatMessageRead(
            id=message.id,
            session_id=message.session_id,
            workspace_id=message.workspace_id,
            owner_id=message.owner_id,
            role=message.role,
            content=message.content,
            message_index=message.message_index,
            created_at=message.created_at,
            citations=[
                ChatMessageCitationRead.model_validate(citation)
                for citation in citations
            ],
        )
        for message, citations in messages_with_citations
    ]
