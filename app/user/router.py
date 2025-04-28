from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from fastapi import APIRouter, Depends, HTTPException, status

from app.auth.dependences import get_current_superuser, get_password_hash, get_current_user
from core.database import get_db
from core.responses import resp_

from . import models, schemas

router = APIRouter()


@router.post(
    "",
    response_model=resp_(schemas.UserResponse),
    status_code=status.HTTP_201_CREATED,
    response_model_exclude_none=True
)
async def create_user(
        user: schemas.UserCreate,
        db: AsyncSession = Depends(get_db),
):
    # 检查用户名是否已存在
    result = await db.execute(select(models.User).where(models.User.username == user.username))
    if result.scalars().first():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Username already registered"
        )

    # 创建新用户
    hashed_password = get_password_hash(user.password)
    db_user = models.User(
        username=user.username,
        hashed_password=hashed_password,
        is_superuser=user.is_superuser
    )
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)
    return {"data": db_user}


@router.get("/me", response_model=schemas.UserResponse)
async def read_users_me(current_user: models.User = Depends(get_current_user)):
    return current_user
