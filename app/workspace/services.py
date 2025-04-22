from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from fastapi import HTTPException, status

from app.permissions.models import Permission, RolePermission
from app.workspace.models import WorkspaceRole


class RoleService:

    @staticmethod
    async def create_role(db: AsyncSession, workspace_id: int, role_name: str):
        """创建角色并分配权限"""
        # 检查角色是否已存在
        result = await db.execute(
            select(WorkspaceRole)
            .where(WorkspaceRole.workspace_id == workspace_id)
            .where(WorkspaceRole.name == role_name)
        )
        existing_role = result.scalars().first()
        if existing_role:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="角色已存在")

        # 创建新角色
        role = WorkspaceRole(name=role_name, workspace_id=workspace_id)
        db.add(role)
        await db.commit()
        await db.refresh(role)

        # 如果是管理员角色，分配所有权限
        if role_name == "administrator":
            await RoleService.assign_all_permissions_to_role(db, role.id)

        return role

    @staticmethod
    async def assign_all_permissions_to_role(db: AsyncSession, role_id: int):
        """为角色分配所有权限"""
        # 获取所有权限
        result = await db.execute(select(Permission))
        permissions = result.scalars().all()

        # 分配权限
        for permission in permissions:
            role_permission = RolePermission(role_id=role_id, permission_id=permission.id)
            db.add(role_permission)

        await db.commit()
