from pydantic import BaseModel
from typing import List, Optional


class CollectionBase(BaseModel):
    name: str
    description: Optional[str] = None


class CollectionCreate(CollectionBase):
    workspace_id: int


class CollectionResponse(CollectionBase):
    id: int

    class Config:
        from_attributes: bool = True


class CollectionItemBase(BaseModel):
    name: str
    image_path: Optional[str] = None


class CollectionItemCreate(CollectionItemBase):
    collection_id: int


class CollectionItemResponse(CollectionItemBase):
    id: int

    class Config:
        from_attributes: bool = True
