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
    collection_id: int


class WorkspaceCollectionItemResponse(WorkspaceCollectionItemBase):
    id: int

    class Config:
        from_attribute: bool = True


