import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.workspaces.models import Workspace


async def create_workspace(
    db: AsyncSession,
    owner_id: uuid.UUID,
    name: str,
    description: str | None,
) -> Workspace:
    workspace = Workspace(
        owner_id=owner_id,
        name=name,
        description=description,
    )

    db.add(workspace)
    await db.commit()
    await db.refresh(workspace)

    return workspace


async def list_workspaces_for_owner(
    db: AsyncSession,
    owner_id: uuid.UUID,
) -> list[Workspace]:
    result = await db.execute(
        select(Workspace)
        .where(Workspace.owner_id == owner_id)
        .order_by(Workspace.created_at.desc())
    )
    return list(result.scalars().all())


async def get_workspace_for_owner(
    db: AsyncSession,
    workspace_id: uuid.UUID,
    owner_id: uuid.UUID,
) -> Workspace | None:
    result = await db.execute(
        select(Workspace).where(
            Workspace.id == workspace_id,
            Workspace.owner_id == owner_id,
        )
    )
    return result.scalar_one_or_none()


async def update_workspace(
    db: AsyncSession,
    workspace: Workspace,
    name: str | None,
    description: str | None,
) -> Workspace:
    if name is not None:
        workspace.name = name

    if description is not None:
        workspace.description = description

    await db.commit()
    await db.refresh(workspace)

    return workspace
