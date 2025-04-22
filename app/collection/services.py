from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from fastapi import HTTPException, status

from app.workspace import models as workspace_models

from . import schemas


class CollectionService:

    @staticmethod
    async def create_collection(db: AsyncSession, collection_data: schemas.CollectionCreate):
        """创建集合"""
        # 检查集合是否已存在
        stmt = select(workspace_models.WorkspaceCollection).where(
            workspace_models.WorkspaceCollection.name == collection_data.name,
            workspace_models.WorkspaceCollection.workspace_id == collection_data.workspace_id
        )
        existing_collection = await db.scalar(stmt)
        if existing_collection:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="集合已存在")

        # 创建新集合
        collection = workspace_models.WorkspaceCollection(**collection_data.dict())
        db.add(collection)
        await db.commit()
        await db.refresh(collection)
        return collection

    @staticmethod
    async def get_collection_by_id(db: AsyncSession, collection_id: int):
        """通过 ID 获取集合"""
        stmt = select(workspace_models.WorkspaceCollection).where(workspace_models.WorkspaceCollection.id == collection_id)
        collection = await db.scalar(stmt)
        if not collection:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="集合不存在")
        return collection

    @staticmethod
    async def get_collections(db: AsyncSession):
        """获取集合列表"""
        stmt = select(workspace_models.WorkspaceCollection)
        collections = await db.scalars(stmt)
        return collections

    @staticmethod
    async def create_collection_item(db: AsyncSession, item_data: schemas.CollectionItemCreate):
        """创建集合项"""
        # 检查集合项是否已存在
        stmt = select(workspace_models.WorkspaceCollectionItem).where(
            workspace_models.WorkspaceCollectionItem.name == item_data.name,
            workspace_models.WorkspaceCollectionItem.collection_id == item_data.collection_id
        )
        existing_item = await db.scalar(stmt)
        if existing_item:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="集合项已存在")

        # 创建新集合项
        item = workspace_models.WorkspaceCollectionItem(**item_data.dict())
        db.add(item)
        await db.commit()
        await db.refresh(item)
        return item

    @staticmethod
    async def get_collection_items(db: AsyncSession, collection_id: int):
        """获取集合中的所有项"""
        stmt = select(workspace_models.WorkspaceCollectionItem).where(
            workspace_models.WorkspaceCollectionItem.collection_id == collection_id
        )
        items = await db.scalars(stmt)
        return items.all()
