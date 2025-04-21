from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship

from core.database import BaseModel


class Workspace(BaseModel):
    """工作区模型"""
    __tablename__ = "workspaces"

    id = Column(Integer, primary_key=True)
    name = Column(String, index=True)
    description = Column(String, nullable=True)

    # 关系
    workspace_users = relationship("WorkspaceUser", back_populates="workspace")
    collections = relationship("WorkspaceCollection", back_populates="workspace")


class WorkspaceRole(BaseModel):
    """工作区角色"""
    __tablename__ = "workspace_roles"

    id = Column(Integer, primary_key=True)
    name = Column(String, index=True)
    workspace_id = Column(Integer, ForeignKey("workspaces.id"))

    # 关系
    workspace_users = relationship("WorkspaceUser", back_populates="role")


class WorkspaceUser(BaseModel):
    """工作区用户"""
    __tablename__ = "workspace_users"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    workspace_id = Column(Integer, ForeignKey("workspaces.id"))
    role_id = Column(Integer, ForeignKey("workspace_roles.id"))

    # 关系
    user = relationship("User", back_populates="workspace_users")
    workspace = relationship("Workspace", back_populates="workspace_users")
    role = relationship("WorkspaceRole", back_populates="workspace_users")


class WorkspaceCollection(BaseModel):
    """工作区 Collections"""
    __tablename__ = "workspace_collections"
    id = Column(Integer, primary_key=True)
    name = Column(String, index=True)
    description = Column(String, nullable=True)
    workspace_id = Column(Integer, ForeignKey("workspaces.id"))

    # 关系
    workspace = relationship("Workspace", back_populates="collections")
    items = relationship("WorkspaceCollectionItem", back_populates="collection")


class WorkspaceCollectionItem(BaseModel):
    __tablename__ = "workspace_collection_items"

    id = Column(Integer, primary_key=True)
    name = Column(String, index=True)
    image_path = Column(String)
    collection_id = Column(Integer, ForeignKey("workspace_collections.id"))

    # 关系
    collection = relationship("WorkspaceCollection", back_populates="items")
