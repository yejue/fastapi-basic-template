from typing import Optional
from pydantic import BaseModel


# 工作区相关模型
class WorkspaceBase(BaseModel):
    name: str
    description: Optional[str] = None


class WorkspaceCreate(WorkspaceBase):
    pass


class WorkspaceResponse(WorkspaceBase):
    id: int

    class Config:
        from_attribute: bool = True


# 角色相关模型
class WorkspaceRoleBase(BaseModel):
    name: str


class WorkspaceRoleCreate(WorkspaceRoleBase):
    pass


class WorkspaceRoleResponse(WorkspaceBase):
    id: int
    workspace_id: int

    class Config:
        from_attribute: bool = True


class WorkspaceInvitation(BaseModel):
    user_id: int
    role_id: int


# 集合相关模型
class WorkspaceCollectionBase(BaseModel):
    name: str
    description: Optional[str] = None


class WorkspaceCollectionCreate(WorkspaceCollectionBase):
    pass


class WorkspaceCollectionResponse(WorkspaceCollectionBase):
    id: int

    class Config:
        from_attribute: bool = True


class WorkspaceCollectionItemBase(BaseModel):
    name: str
    image_path: Optional[str] = None


class WorkspaceCollectionItemCreate(WorkspaceCollectionItemBase):
    collection_id: Optional[int] = None


class WorkspaceCollectionItemResponse(WorkspaceCollectionItemBase):
    id: int

    class Config:
        from_attribute: bool = True


# 工作区权限相关
class WorkspacePermissionBase(BaseModel):
    path: str
    action: str
    allow: bool = True


class WorkspaceRolePermissionCreate(WorkspacePermissionBase):
    role_id: Optional[int] = None       # 从路径参数获取
    workspace_id: Optional[int] = None  # 从路径参数获取


class WorkspaceUserPermissionCreate(WorkspacePermissionBase):
    user_id: Optional[int] = None       # 从路径参数获取
    workspace_id: Optional[int] = None  # 从路径参数获取


class WorkspacePermissionResponse(WorkspacePermissionBase):
    id: int

    class Config:
        from_attribute = True


class WorkspaceUserPermissionDetails(BaseModel):
    user_permissions: list[WorkspacePermissionBase]
    role_permissions: list[WorkspacePermissionBase]
