from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependences import get_current_superuser, get_current_user
from app.user.models import User
from core.database import get_db

from . import models, schemas

router = APIRouter()


@router.get("/permissions", response_model=List[schemas.PermissionResponse])
async def get_permissions(
        db: AsyncSession = Depends(get_db),
        current_user: User = Depends(get_current_superuser)
):
    """获取所有权限（仅限超级用户）"""
    result = await db.execute(select(models.Permission))
    permissions = result.scalars().all()
    return permissions


@router.post("/roles/{role_id}/permissions", status_code=status.HTTP_200_OK)
async def assign_permission_to_role(
        role_id: int,
        permission_data: schemas.RolePermissionAssign,
        db: AsyncSession = Depends(get_db),
        current_user: User = Depends(get_current_superuser)
):
    """将权限分配给角色（仅限超级用户）"""
    from app.workspace.models import WorkspaceRole

    # 验证角色是否存在
    result = await db.execute(
        select(WorkspaceRole)
        .where(WorkspaceRole.id == role_id)
    )
    role = result.scalars().first()
    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="角色不存在"
        )

    # 验证权限是否存在
    result = await db.execute(
        select(models.Permission)
        .where(models.Permission.id == permission_data.permission_id)
    )
    permission = result.scalars().first()
    if not permission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="权限不存在"
        )

    # 添加权限到角色
    role.permissions.append(permission)

    await db.commit()

    return {"message": "权限分配成功"}
