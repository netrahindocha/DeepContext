from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db_session
from app.modules.auth.schemas import UserCreate, UserRead
from app.modules.auth.service import create_user, get_user_by_email

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


@router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def register_user(
    payload: UserCreate,
    db: AsyncSession = Depends(get_db_session),
) -> UserRead:
    existing_user = await get_user_by_email(db, payload.email)

    if existing_user is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email is already registered",
        )

    user = await create_user(db, payload.email, payload.password)
    return UserRead.model_validate(user)
