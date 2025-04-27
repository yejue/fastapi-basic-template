from typing import List

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import APIRouter, Depends, HTTPException, status

from app.auth.dependences import get_current_user
from app.user.models import User
from app.permissions.engine import require_workspace_permission, WorkspacePermissionEngine

from core.database import get_db
from core.responses import resp_

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
    status_code=status.HTTP_201_CREATED
)
async def create_collection_in_workspace(
    workspace_id: int,
    collection_data: schemas.WorkspaceCollectionCreate,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_workspace_permission("/workspaces/{workspace_id}/collections", action="create"))
):
    """在工作区中创建集合"""
    return await services.WorkspaceCollectionService.create_collection(db, workspace_id, collection_data)


@router.delete(
    "/user-workspaces/{workspace_id}/collections/{collection_id}",
)
async def delete_collection_in_workspace(
    workspace_id: int,
    collection_id: int,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_workspace_permission("/workspaces/{workspace_id}/collections/{collection_id}", action="delete"))
):
    return await services.WorkspaceCollectionService.delete_collection_by_id(db, collection_id)


@router.post(
    "/user-workspaces/{workspace_id}/collections/{collection_id}/items",
    response_model=schemas.WorkspaceCollectionItemResponse,
    status_code=status.HTTP_201_CREATED
)
async def create_item_in_workspace(
    workspace_id: int,
    collection_id: int,
    item_data: schemas.WorkspaceCollectionItemCreate,
    db: AsyncSession = Depends(get_db),
    _=Depends(
        require_workspace_permission(
            "/workspaces/{workspace_id}/collections/{collection_id}/items}",
            action="create")
    )
):
    item_data.collection_id = collection_id
    return await services.WorkspaceCollectionService.create_collection_item(db, item_data)


@router.delete(
    "/user-workspaces/{workspace_id}/collections/{collection_id}/items/{item_id}",
    status_code=status.HTTP_200_OK
)
async def delete_item_in_workspace(
    workspace_id: int,
    collection_id: int,
    item_id: int,
    db: AsyncSession = Depends(get_db),
    _=Depends(
        require_workspace_permission(
            "/workspaces/{workspace_id}/collections/{collection_id}/items/{item_id}",
            action="delete")
    )
):
    return await services.WorkspaceCollectionService.delete_collection_item(db, item_id)


@router.get(
    "/user-workspaces/{workspace_id}/collections",
    response_model=List[schemas.WorkspaceCollectionResponse]
)
async def get_workspace_collections(
    workspace_id: int,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_workspace_permission("/workspaces/{workspace_id}/collections", action="read"))
):
    return await services.WorkspaceCollectionService.get_collections(db, workspace_id=workspace_id)


@router.get(
    "/user-workspaces/{workspace_id}/collections/{collection_id}/items",
    response_model=resp_(List[schemas.WorkspaceCollectionItemResponse])
)
async def get_workspace_collection_items(
    workspace_id: int,
    collection_id: int,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_workspace_permission("/workspaces/{workspace_id}/collections/{collection_id}/items", action="read"))
):
    return {"data": await services.WorkspaceCollectionService.get_collection_items(db, collection_id)}


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


@router.post("/workspaces/{workspace_id}/roles/{role_id}/permissions", status_code=status.HTTP_201_CREATED)
async def assign_role_permission(
    workspace_id: int,
    role_id: int,
    permission_data: schemas.WorkspaceRolePermissionCreate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
    _=Depends(require_workspace_permission("/workspaces/{workspace_id}/roles/{role_id}/permissions", "create"))
):
    """为工作区内的角色分配权限"""
    permission_data.role_id = role_id
    permission_data.workspace_id = workspace_id

    # 校验使用者权限
    engine = WorkspacePermissionEngine(db, current_user)
    has_permission = await engine.check_permission(
        path=permission_data.path,
        action=permission_data.action
    )
    if not has_permission:
        raise HTTPException(status_code=403, detail="没有分配该权限的权限")

    return await services.WorkspacePermissionService.assign_role_permission(db, permission_data)


@router.post("/workspaces/{workspace_id}/users/{user_id}/permissions", status_code=status.HTTP_201_CREATED)
async def assign_user_permission(
    workspace_id: int,
    user_id: int,
    permission_data: schemas.WorkspaceUserPermissionCreate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
    _=Depends(require_workspace_permission("/workspaces/{workspace_id}/users/{user_id}/permissions", "create"))
):
    """为工作区内的用户分配权限"""
    permission_data.workspace_id = workspace_id
    permission_data.user_id = user_id

    # 校验使用者权限
    engine = WorkspacePermissionEngine(db, current_user)
    has_permission = await engine.check_permission(
        path=permission_data.path,
        action=permission_data.action
    )
    if not has_permission:
        raise HTTPException(status_code=403, detail="没有分配该权限的权限")

    return await services.WorkspacePermissionService.assign_user_permission(db, permission_data)
