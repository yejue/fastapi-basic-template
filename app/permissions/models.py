from typing import Dict, Any, Optional
from sqlalchemy import Column, Integer, String, JSON, ForeignKey, Boolean, Table
from sqlalchemy.orm import relationship

from core.database import BaseModel


# 角色-权限多对多关系表
class RolePermission(BaseModel):
    """角色权限多对多关系模型"""
    __tablename__ = "role_permissions"

    role_id = Column(Integer, ForeignKey("workspace_roles.id"), primary_key=True)
    permission_id = Column(Integer, ForeignKey("permissions.id"), primary_key=True)

    # 关系
    role = relationship("WorkspaceRole", back_populates="role_permissions", overlaps="permissions")
    permission = relationship("Permission", back_populates="role_permissions", overlaps="permissions")


class Permission(BaseModel):
    """权限定义模型"""
    __tablename__ = "permissions"

    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, index=True)  # 如：workspace.read, workspace.update
    description = Column(String, nullable=True)

    role_permissions = relationship("RolePermission", back_populates="permission")
    roles = relationship("WorkspaceRole", secondary="role_permissions", back_populates="permissions", overlaps="role")


class AclEntry(BaseModel):
    """访问控制列表条目"""
    __tablename__ = "acl_entries"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    resource_type = Column(String)  # 资源类型，如 workspace
    resource_id = Column(Integer)   # 资源 ID
    permission_id = Column(Integer, ForeignKey("permissions.id"))
    allow = Column(Boolean, default=True)  # 允许或拒绝

    # 关系
    user = relationship("User", backref="acl_entries")
    permission = relationship("Permission")


class AbacPolicy(BaseModel):
    """基于属性的访问控制策略模型"""
    __tablename__ = "abac_policies"

    id = Column(Integer, primary_key=True)
    name = Column(String, index=True)
    resource_type = Column(String)
    action = Column(String)
    condition = Column(JSON)  # 例如 {"user.department": "== 'AI'", "resource.level": "in ['low', 'medium']"}
    workspace_id = Column(Integer, ForeignKey("workspaces.id"), nullable=True)

    # 关系
    workspace = relationship("Workspace", backref="abac_policies")
