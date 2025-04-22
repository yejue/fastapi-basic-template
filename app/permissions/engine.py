from typing import Dict, Any, Optional, List
import jmespath
from datetime import datetime
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.user.models import User
from app.workspace.models import Workspace, WorkspaceUser, WorkspaceRole

from . import models


class PermissionEngine:
    def __init__(self, db: AsyncSession, user: User, resource: Any, context: Optional[Dict[str, Any]] = None):
        self.db = db
        self.user = user
        self.resource = resource
        self.context = context or {
            "time": datetime.now(),
            "weekday": datetime.now().weekday()
        }

    async def evaluate(self, action: str) -> bool:
        """评估用户是否有权限执行操作"""
        # 超级用户拥有所有权限
        if self.user.is_superuser:
            print(">>> 校验 is_superuser 通过")
            return True
        print(">>> 校验 is_superuser 未通过")

        # 检查基于角色的权限 (RBAC)
        if await self._rbac_allows(action):
            print(">>> 校验 _rbac_allows 通过")
            return True
        print(">>> 校验 _rbac_allows 未通过")

        # 检查访问控制列表权限 (ACL)
        if await self._acl_allows(action):
            print(">>> 校验 _acl_allows 通过")
            return True
        print(">>> 校验 _acl_allows 未通过")

        # 检查基于属性的访问控制 (ABAC)
        if await self._abac_allows(action):
            print(">>> 校验 _abac_allows 通过")
            return True
        print(">>> 校验 _abac_allows 未通过")

        return False

    async def _rbac_allows(self, action: str) -> bool:
        """基于角色的权限检查"""
        # 获取资源类型
        resource_type = self.resource.__class__.__name__.lower()

        # 构建完整的权限名称
        permission_name = f"{resource_type}.{action}"

        # 对于 workspace 资源
        if isinstance(self.resource, Workspace):
            # 检查用户是否属于该工作区
            result = await self.db.execute(
                select(WorkspaceUser)
                .where(WorkspaceUser.workspace_id == self.resource.id)
                .where(WorkspaceUser.user_id == self.user.id)
            )
            workspace_user = result.scalars().first()

            # 如果用户不在工作区内，则拒绝访问
            if not workspace_user:
                return False

            # 获取用户角色
            result = await self.db.execute(
                select(WorkspaceRole)
                .where(WorkspaceRole.id == workspace_user.role_id)
            )
            role = result.scalars().first()

            if not role:
                return False

            # 检查角色是否有该权限
            result = await self.db.execute(
                select(models.Permission)
                .join(models.RolePermission)
                .where(models.RolePermission.role_id == role.id)
                .where(models.Permission.name == permission_name)
            )
            permission = result.scalars().first()

            return permission is not None

        return False

    async def _acl_allows(self, action: str) -> bool:
        """访问控制列表权限检查"""
        resource_type = self.resource.__class__.__name__.lower()
        resource_id = getattr(self.resource, "id", None)

        if not resource_id:
            return False

        # 查找相关的权限
        result = await self.db.execute(
            select(models.Permission)
            .where(models.Permission.name == f"{resource_type}.{action}")
        )
        permission = result.scalars().first()

        if not permission:
            return False

        # 查找 ACL 条目
        result = await self.db.execute(
            select(models.AclEntry)
            .where(models.AclEntry.user_id == self.user.id)
            .where(models.AclEntry.resource_type == resource_type)
            .where(models.AclEntry.resource_id == resource_id)
            .where(models.AclEntry.permission_id == permission.id)
        )
        acl_entry = result.scalars().first()

        if acl_entry and acl_entry.allow:
            return True

        return False

    async def _abac_allows(self, action: str) -> bool:
        """基于属性的访问控制检查"""
        # 获取适用于此资源类型和操作的所有 ABAC 策略
        resource_type = self.resource.__class__.__name__.lower()

        # 查询适用的策略
        result = await self.db.execute(
            select(models.AbacPolicy)
            .where(models.AbacPolicy.resource_type == resource_type)
            .where(models.AbacPolicy.action == action)
        )
        policies = result.scalars().all()

        # 针对工作区特定的策略
        if hasattr(self.resource, 'id') and hasattr(self.resource, '__tablename__') and self.resource.__tablename__ == 'workspaces':
            result = await self.db.execute(
                select(models.AbacPolicy)
                .where(models.AbacPolicy.resource_type == resource_type)
                .where(models.AbacPolicy.action == action)
                .where(models.AbacPolicy.workspace_id == self.resource.id)
            )
            workspace_policies = result.scalars().all()
            policies.extend(workspace_policies)

        # 评估每个策略
        for policy in policies:
            if await self._evaluate_policy(policy):
                return True

        return False

    async def _evaluate_policy(self, policy: models.AbacPolicy) -> bool:
        """评估单个 ABAC 策略"""
        if not policy.condition:
            return False

        for attr, expr in policy.condition.items():
            value = None
            if attr.startswith("user."):
                value = self._get_nested_attr(self.user, attr[5:])
            elif attr.startswith("resource."):
                value = self._get_nested_attr(self.resource, attr[9:])
            elif attr.startswith("context."):
                key = attr[8:]
                value = self.context.get(key)

            # 使用安全的方式评估表达式
            try:
                result = eval(f"{repr(value)} {expr}")
                if not result:
                    return False
            except:
                return False

        return True

    def _get_nested_attr(self, obj, attr_path):
        """安全地获取对象的嵌套属性"""
        try:
            return jmespath.search(attr_path, obj.__dict__)
        except:
            return None
