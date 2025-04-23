from typing import List

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import APIRouter, Depends, HTTPException, status, Request

from app.auth.dependences import get_current_user
from app.user.models import User
from app.permissions.engine import require_workspace_permission


from core.database import get_db

from . import schemas, models, services


router = APIRouter()


@router.post(
    "/user-workspaces",
    response_model=schemas.WorkspaceResponse,
    status_code=status.HTTP_201_CREATED
)
async def create_workspace(
    workspace: schemas.WorkspaceCreate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """创建工作区"""
    return await services.WorkspaceService.create_workspace(db, workspace, current_user.id)


@router.get("/user-workspaces", response_model=List[schemas.WorkspaceResponse])
async def get_user_workspaces(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """获取当前用户工作区列表"""
    # 获取用户所在的所有工作区
    result = await db.execute(
        select(models.Workspace)
        .join(models.WorkspaceUser)
        .where(models.WorkspaceUser.user_id == current_user.id)
    )
    workspaces = result.scalars().all()
    return workspaces


@router.post(
    "/user-workspaces/{workspace_id}/collections",
    response_model=schemas.WorkspaceCollectionResponse,
)
async def create_collection_in_workspace(
    workspace_id: int,
    collection_data: schemas.WorkspaceCollectionCreate,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_workspace_permission("/workspaces/{workspace_id}/collections", action="create"))
):
    """在工作区中创建集合"""
    return await services.WorkspaceCollectionService.create_collection(db, workspace_id, collection_data)


@router.get("/{workspace_id}", response_model=schemas.WorkspaceResponse)
async def get_workspace(
    workspace_id: int,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_workspace_permission("/workspaces/{workspace_id}", action="read"))
):
    """获取工作区详情"""
    return await services.WorkspaceService.get_workspace_by_id(db, workspace_id)


@router.post("/{workspace_id}/invitations", status_code=status.HTTP_201_CREATED)
async def invite_user(
    workspace_id: int,
    invitation: schemas.WorkspaceInvitation,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user)
):
    # 验证当前用户是否是工作区管理员
    result = await db.execute(
        select(models.WorkspaceUser)
        .join(models.WorkspaceRole)
        .where(models.WorkspaceUser.workspace_id == workspace_id)
        .where(models.WorkspaceUser.user_id == current_user.id)
        .where(models.WorkspaceRole.name == "administrator")
    )
    if not result.scalars().first():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can invite users"
        )

    # 验证被邀请的用户是否存在
    result = await db.execute(
        select(User)
        .where(User.id == invitation.user_id)
    )

    user = result.scalars().first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # 验证角色是否存在于该工作区
    result = await db.execute(
        select(models.WorkspaceRole)
        .where(models.WorkspaceRole.id == invitation.role_id)
        .where(models.WorkspaceRole.workspace_id == workspace_id)
    )
    role = result.scalars().first()
    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Role not found in this workspace"
        )

    # 检查用户是否已在工作区
    result = await db.execute(
        select(models.WorkspaceUser)
        .where(models.WorkspaceUser.workspace_id == workspace_id)
        .where(models.WorkspaceUser.user_id == invitation.user_id)
    )
    if result.scalars().first():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User already in workspace"
        )

    # 创建工作区用户关系
    workspace_user = models.WorkspaceUser(
        user_id=invitation.user_id,
        workspace_id=workspace_id,
        role_id=invitation.role_id
    )
    db.add(workspace_user)
    await db.commit()

    return {"message": "User invited successfully"}
