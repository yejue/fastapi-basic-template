from sqlalchemy import Column, Integer, String, Boolean
from sqlalchemy.orm import relationship

from core.database import BaseModel


class User(BaseModel):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    username = Column(String(50), doc="用户名", default="未命名")
    hashed_password = Column(String(200))
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)

    workspace_users = relationship("WorkspaceUser", back_populates="user")

    def __repr__(self):
        return f"User(id={self.id})"
