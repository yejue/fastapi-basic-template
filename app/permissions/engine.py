from typing import Optional

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from fastapi import Depends, HTTPException, status, Request

from app.user.models import User
from app.workspace.models import WorkspaceUser
from app.permissions.models import WorkspaceUserPermissions, WorkspaceRolePermissions
from app.auth.dependences import get_current_user, get_db


class WorkspacePermissionEngine:
    """权限校验引擎"""

    def __init__(self, db: AsyncSession, user: User):
        self.db = db
        self.user = user

    async def check_permission(self, path: str, action: str) -> bool:
        """检查用户是否有权限访问指定路径和执行指定操作"""
        # 超级用户跳过权限检查
        if self.user.is_superuser:
            return True

        # 提取工作区ID
        workspace_id = self._extract_workspace_id(path)
        if not workspace_id:
            return False  # 无法确定工作区ID

        # 获取用户在该工作区的角色
        stmt = select(WorkspaceUser).where(
            WorkspaceUser.user_id == self.user.id,
            WorkspaceUser.workspace_id == workspace_id
        )
        workspace_user = await self.db.scalar(stmt)

        if not workspace_user:
            return False  # 用户不在该工作区

        # 检查角色权限
        role_id = workspace_user.role_id
        stmt = select(WorkspaceRolePermissions).where(
            WorkspaceRolePermissions.workspace_role_id == role_id
        )
        role_permissions = await self.db.scalars(stmt)

        for perm in role_permissions:
            if self._path_matches(path, perm.path) and (perm.action == "*" or perm.action == action) and perm.allow:
                return True

        # 检查用户直接权限
        stmt = select(WorkspaceUserPermissions).where(
            WorkspaceUserPermissions.workspace_user_id == workspace_user.id
        )
        user_permissions = await self.db.scalars(stmt)

        for perm in user_permissions:
            if self._path_matches(path, perm.path) and (perm.action == "*" or perm.action == action) and perm.allow:
                return True

        return False

    @staticmethod
    def _extract_workspace_id(path: str) -> Optional[int]:
        """从路径中提取工作区ID"""
        parts = path.split('/')
        for i, part in enumerate(parts):
            if part == "workspaces" and i + 1 < len(parts):
                try:
                    return int(parts[i + 1])
                except ValueError:
                    return None
        return None

    @staticmethod
    def _path_matches(request_path: str, permission_path: str) -> bool:
        """检查请求路径是否匹配权限路径"""
        # 特殊情况：权限路径以 /* 结尾，表示匹配该路径下的所有子路径
        if permission_path.endswith("/*"):
            base_path = permission_path[:-2]
            return request_path == base_path or request_path.startswith(base_path + "/")

        # 特殊情况：完全通配符
        if permission_path == "*":
            return True

        # 将路径转换为正则表达式模式
        import re
        pattern = "^"

        # 拆分路径段
        path_segments = permission_path.split("/")
        for segment in path_segments:
            if segment == "*":
                # 单星号匹配一个路径段
                pattern += "/[^/]*"
            elif segment.startswith("{") and segment.endswith("}"):
                # 参数占位符匹配一个路径段
                pattern += "/[^/]+"
            elif segment:
                # 普通路径段精确匹配
                pattern += "/" + re.escape(segment)

        pattern += "$"

        # 移除多余的起始斜杠
        pattern = pattern.replace("^/", "^")
        print(f"target: {request_path}, pattern: {pattern}")
        # 匹配路径
        return re.match(pattern, request_path) is not None


def require_workspace_permission(path: str, action: str):
    """权限校验依赖"""

    async def check_permission(
            request: Request,
            current_user: User = Depends(get_current_user),
            db: AsyncSession = Depends(get_db)
    ):
        # 替换路径中的参数
        actual_path = path
        for param_name, param_value in request.path_params.items():
            actual_path = actual_path.replace(f"{{{param_name}}}", str(param_value))

        # 创建权限引擎并检查权限
        engine = WorkspacePermissionEngine(db, current_user)
        has_permission = await engine.check_permission(actual_path, action)

        if not has_permission:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="没有足够的权限执行此操作"
            )

        return True

    return check_permission
