from typing import List, Optional, Dict, Any
from pydantic import BaseModel


class PermissionBase(BaseModel):
    name: str
    description: Optional[str] = None


class PermissionCreate(PermissionBase):
    pass


class PermissionResponse(PermissionBase):
    id: int

    class Config:
        from_attribute = True


class AclEntryBase(BaseModel):
    user_id: int
    resource_type: str
    resource_id: int
    permission_id: int
    allow: bool = True


class RolePermissionAssign(BaseModel):
    permission_id: int

