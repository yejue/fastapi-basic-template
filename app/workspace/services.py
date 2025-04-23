from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from fastapi import HTTPException, status

from app.permissions.models import WorkspaceRolePermissions, WorkspaceUserPermissions
from . import schemas, models


class WorkspaceService:

    @staticmethod
    async def get_workspace_by_id(db: AsyncSession, workspace_id: int):
        """通过ID获取工作区"""
        stmt = select(models.Workspace).where(models.Workspace.id == workspace_id)
        workspace = await db.scalar(stmt)
        if not workspace:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="该工作区不存在")
        return workspace

    @staticmethod
    async def create_workspace(db: AsyncSession, workspace_data: schemas.WorkspaceCreate, user_id: int):
        """创建工作区"""
        # 创建工作区
        workspace = models.Workspace(
            name=workspace_data.name,
            description=workspace_data.description
        )
        db.add(workspace)
        await db.flush()

        # 创建默认角色
        roles = await RoleService.create_default_roles(db, workspace.id)

        # 为当前用户分配管理员角色
        admin_role = next((role for role in roles if role.name == "administrator"), None)
        if admin_role:
            workspace_user = models.WorkspaceUser(
                user_id=user_id,
                workspace_id=workspace.id,
                role_id=admin_role.id
            )
            db.add(workspace_user)

        await db.commit()
        await db.refresh(workspace)
        return workspace

    @staticmethod
    async def get_user_workspaces(db: AsyncSession, user_id: int):
        """获取用户所在的工作区列表"""
        stmt = select(models.Workspace).join(
            models.WorkspaceUser,
            models.Workspace.id == models.WorkspaceUser.workspace_id
        ).where(models.WorkspaceUser.user_id == user_id)
        workspaces = await db.scalars(stmt)
        return workspaces.all()


class RoleService:

    @staticmethod
    async def create_default_roles(db: AsyncSession, workspace_id: int):
        """创建工作区默认角色"""
        roles = []
        role_names = ["administrator", "member", "viewer"]

        for role_name in role_names:
            role = models.WorkspaceRole(
                name=role_name,
                workspace_id=workspace_id
            )
            db.add(role)
            roles.append(role)

        await db.flush()

        # 为管理员角色分配所有权限
        admin_role = next((role for role in roles if role.name == "administrator"), None)
        if admin_role:
            await RoleService.assign_admin_permissions(db, admin_role.id, workspace_id)

        # 为成员角色分配部分权限
        member_role = next((role for role in roles if role.name == "member"), None)
        if member_role:
            await RoleService.assign_member_permissions(db, member_role.id, workspace_id)

        # 为查看者角色分配只读权限
        viewer_role = next((role for role in roles if role.name == "viewer"), None)
        if viewer_role:
            await RoleService.assign_viewer_permissions(db, viewer_role.id, workspace_id)

        return roles

    @staticmethod
    async def assign_admin_permissions(db: AsyncSession, role_id: int, workspace_id: int) -> None:
        """为管理员角色分配所有权限"""
        # 管理员拥有所有权限
        admin_permission = WorkspaceRolePermissions(
            workspace_role_id=role_id,
            path=f"/workspaces/{workspace_id}/*",
            action="*",
            allow=True
        )
        db.add(admin_permission)

    @staticmethod
    async def assign_member_permissions(db: AsyncSession, role_id: int, workspace_id: int) -> None:
        """为成员角色分配部分权限"""
        # 成员可以读取和创建，但不能删除
        permissions = [
            WorkspaceRolePermissions(workspace_role_id=role_id, path=f"/workspaces/{workspace_id}", action="read", allow=True),
            WorkspaceRolePermissions(workspace_role_id=role_id, path=f"/workspaces/{workspace_id}", action="create", allow=True),
            WorkspaceRolePermissions(workspace_role_id=role_id, path=f"/workspaces/{workspace_id}", action="update", allow=True),
        ]
        db.add_all(permissions)

    @staticmethod
    async def assign_viewer_permissions(db: AsyncSession, role_id: int, workspace_id: int) -> None:
        """为查看者角色分配只读权限"""
        # 查看者只有读取权限
        permissions = [
            WorkspaceRolePermissions(workspace_role_id=role_id, path=f"/workspaces/{workspace_id}", action="read", allow=True),
        ]
        db.add_all(permissions)


class WorkspaceCollectionService:

    @staticmethod
    async def create_collection(db: AsyncSession, workspace_id: int, collection_data: schemas.WorkspaceCollectionCreate):
        """在工作区中创建集合"""
        # 检查集合是否已存在
        stmt = select(models.WorkspaceCollection).where(
            models.WorkspaceCollection.name == collection_data.name,
            models.WorkspaceCollection.workspace_id == workspace_id
        )
        existing_collection = await db.scalar(stmt)
        if existing_collection:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="集合已存在")

        # 创建新集合
        collection = models.WorkspaceCollection(**collection_data.dict(), workspace_id=workspace_id)
        db.add(collection)
        await db.commit()
        await db.refresh(collection)
        return collection

    @staticmethod
    async def get_collection_by_id(db: AsyncSession, collection_id: int):
        """通过 ID 获取集合"""
        stmt = select(models.WorkspaceCollection).where(models.WorkspaceCollection.id == collection_id)
        collection = await db.scalar(stmt)
        if not collection:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="集合不存在")
        return collection

    @staticmethod
    async def get_collections(db: AsyncSession, workspace_id: int):
        """获取工作区中的集合列表"""
        stmt = select(models.WorkspaceCollection).where(models.WorkspaceCollection.workspace_id == workspace_id)
        collections = await db.scalars(stmt)
        return collections.all()

    @staticmethod
    async def create_collection_item(db: AsyncSession, item_data: schemas.WorkspaceCollectionItemCreate):
        """创建集合项"""
        # 检查集合项是否已存在
        stmt = select(models.WorkspaceCollectionItem).where(
            models.WorkspaceCollectionItem.name == item_data.name,
            models.WorkspaceCollectionItem.collection_id == item_data.collection_id
        )
        existing_item = await db.scalar(stmt)
        if existing_item:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="集合项已存在")

        # 创建新集合项
        item = models.WorkspaceCollectionItem(**item_data.model_dump())
        db.add(item)
        await db.commit()
        await db.refresh(item)
        return item

    @staticmethod
    async def get_collection_items(db: AsyncSession, collection_id: int):
        """获取集合中的所有项"""
        stmt = select(models.WorkspaceCollectionItem).where(
            models.WorkspaceCollectionItem.collection_id == collection_id
        )
        items = await db.scalars(stmt)
        return items.all()


class WorkspacePermissionService:

    @staticmethod
    async def assign_user_permission(
            db: AsyncSession,
            workspace_id: int,
            user_id: int,
            path: str,
            action: str,
            allow: bool = True
    ):
        """为用户分配工作区内的权限"""
        # 检查用户是否在工作区内
        stmt = select(models.WorkspaceUser).where(
            models.WorkspaceUser.workspace_id == workspace_id,
            models.WorkspaceUser.user_id == user_id
        )
        workspace_user = await db.scalar(stmt)

        if not workspace_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="用户不在该工作区内"
            )

        # 检查权限是否已存在
        stmt = select(WorkspaceUserPermissions).where(
            WorkspaceUserPermissions.workspace_user_id == workspace_user.id,
            WorkspaceUserPermissions.path == path,
            WorkspaceUserPermissions.action == action
        )
        existing_permission = await db.scalar(stmt)

        if existing_permission:
            # 更新现有权限
            existing_permission.allow = allow
        else:
            # 创建新权限
            permission = WorkspaceUserPermissions(
                workspace_user_id=workspace_user.id,
                path=path,
                action=action,
                allow=allow
            )
            db.add(permission)

        await db.commit()
        return {"message": "权限分配成功"}

    @staticmethod
    async def get_user_permissions(db: AsyncSession, workspace_id: int, user_id: int):
        """获取用户在工作区内的所有权限"""
        # 获取用户在工作区的关系
        stmt = select(models.WorkspaceUser).where(
            models.WorkspaceUser.workspace_id == workspace_id,
            models.WorkspaceUser.user_id == user_id
        )
        workspace_user = await db.scalar(stmt)

        if not workspace_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="用户不在该工作区内"
            )

        # 获取用户直接权限
        stmt = select(WorkspaceUserPermissions).where(
            WorkspaceUserPermissions.workspace_user_id == workspace_user.id
        )
        user_permissions = await db.scalars(stmt)

        # 获取角色权限
        stmt = select(WorkspaceRolePermissions).where(
            WorkspaceRolePermissions.role_id == workspace_user.role_id
        )
        role_permissions = await db.scalars(stmt)

        return {
            "user_permissions": user_permissions.all(),
            "role_permissions": role_permissions.all()
        }
