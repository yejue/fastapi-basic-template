from sqlalchemy import Column, Integer, String, ForeignKey, Boolean, DateTime
from sqlalchemy.orm import relationship

from core.database import BaseModel


class WorkspaceUserPermissions(BaseModel):
    __tablename__ = "workspace_user_permissions"

    id = Column(Integer, primary_key=True)
    workspace_user_id = Column(Integer, ForeignKey("workspace_users.id"))
    path = Column(String, nullable=False)
    action = Column(String, nullable=False)
    allow = Column(Boolean, default=True)

    workspace_user = relationship("WorkspaceUser", back_populates="workspace_permissions")


class WorkspaceRolePermissions(BaseModel):
    __tablename__ = "workspace_role_permissions"

    id = Column(Integer, primary_key=True)
    workspace_role_id = Column(Integer, ForeignKey("workspace_roles.id"))
    path = Column(String, nullable=False)
    action = Column(String, nullable=False)
    allow = Column(Boolean, default=True)

    workspace_roles = relationship("WorkspaceRole", back_populates="workspace_permissions")
