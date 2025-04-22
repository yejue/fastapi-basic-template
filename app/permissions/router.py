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


@router.post("/acl", response_model=schemas.AclEntryResponse, status_code=status.HTTP_201_CREATED)
async def create_acl_entry(
        acl_entry: schemas.AclEntryCreate,
        db: AsyncSession = Depends(get_db),
        current_user: User = Depends(get_current_superuser)
):
    """创建 ACL 条目（仅限超级用户）"""

    # 验证权限是否存在
    result = await db.execute(
        select(models.Permission)
        .where(models.Permission.id == acl_entry.permission_id)
    )
    permission = result.scalars().first()
    if not permission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="权限不存在"
        )

    # 验证用户是否存在
    result = await db.execute(
        select(User)
        .where(User.id == acl_entry.user_id)
    )
    user = result.scalars().first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )

    # 创建 ACL 条目
    db_acl_entry = models.AclEntry(
        user_id=acl_entry.user_id,
        resource_type=acl_entry.resource_type,
        resource_id=acl_entry.resource_id,
        permission_id=acl_entry.permission_id,
        allow=acl_entry.allow
    )

    db.add(db_acl_entry)
    await db.commit()
    await db.refresh(db_acl_entry)

    return db_acl_entry


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


@router.post("/abac-policies", response_model=schemas.AbacPolicyResponse, status_code=status.HTTP_201_CREATED)
async def create_abac_policy(
        policy: schemas.AbacPolicyCreate,
        db: AsyncSession = Depends(get_db),
        current_user: User = Depends(get_current_superuser)
):
    """创建 ABAC 策略（仅限超级用户）"""

    # 创建 ABAC 策略
    db_policy = models.AbacPolicy(
        name=policy.name,
        resource_type=policy.resource_type,
        action=policy.action,
        condition=policy.condition,
        workspace_id=policy.workspace_id
    )

    db.add(db_policy)
    await db.commit()
    await db.refresh(db_policy)

    return db_policy
