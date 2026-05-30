from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User, UserCreate, UserProfile, UserProfileRead, UserRead

router = APIRouter()


@router.post("/users", response_model=UserRead, status_code=201)
async def create_user(
    body: UserCreate,
    db: AsyncSession = Depends(get_db),
) -> User:
    result = await db.execute(select(User).where(User.email == body.email))
    existing = result.scalar_one_or_none()
    if existing:
        return existing
    user = User(email=body.email)
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


@router.get("/users/{user_id}/profile", response_model=UserProfileRead)
async def get_user_profile(
    user_id: str,
    db: AsyncSession = Depends(get_db),
) -> UserProfile:
    try:
        uid = UUID(user_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid user ID format")
    result = await db.execute(
        select(UserProfile).where(UserProfile.user_id == uid)
    )
    profile = result.scalar_one_or_none()
    if not profile:
        raise HTTPException(status_code=404, detail="User profile not found")
    return profile
