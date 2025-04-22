from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from fastapi import HTTPException, status

from app.permissions.models import Permission, RolePermission

from . import schemas, models


class RoleService:

    @staticmethod
    async def create_role(db: AsyncSession, workspace_id: int, role_name: str):
        """创建角色并分配权限"""
        # 检查角色是否已存在
        result = await db.execute(
            select(models.WorkspaceRole)
            .where(models.WorkspaceRole.workspace_id == workspace_id)
            .where(models.WorkspaceRole.name == role_name)
        )
        existing_role = result.scalars().first()
        if existing_role:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="角色已存在")

        # 创建新角色
        role = models.WorkspaceRole(name=role_name, workspace_id=workspace_id)
        db.add(role)
        await db.commit()
        await db.refresh(role)

        # 如果是管理员角色，分配所有权限
        if role_name == "administrator":
            await RoleService.assign_all_permissions_to_role(db, role.id)

        return role

    @staticmethod
    async def assign_all_permissions_to_role(db: AsyncSession, role_id: int):
        """为角色分配所有权限"""
        # 获取所有权限
        result = await db.execute(select(Permission))
        permissions = result.scalars().all()

        # 分配权限
        for permission in permissions:
            role_permission = RolePermission(role_id=role_id, permission_id=permission.id)
            db.add(role_permission)

        await db.commit()


class WorkspaceCollectionService:

    @staticmethod
    async def create_collection(db: AsyncSession, workspace_id: int, collection_data: schemas.WorkspaceCollectionCreate):
        """在工作区中创建集合"""
        # 检查集合是否已存在
        stmt = select(models.WorkspaceCollection).where(
            models.WorkspaceCollection.name == collection_data.name,
            models.WorkspaceCollection.workspace_id == workspace_id
        )
        existing_collection = await db.scalar(stmt)
        if existing_collection:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="集合已存在")

        # 创建新集合
        collection = models.WorkspaceCollection(**collection_data.dict(), workspace_id=workspace_id)
        db.add(collection)
        await db.commit()
        await db.refresh(collection)
        return collection

    @staticmethod
    async def get_collection_by_id(db: AsyncSession, collection_id: int):
        """通过 ID 获取集合"""
        stmt = select(models.WorkspaceCollection).where(models.WorkspaceCollection.id == collection_id)
        collection = await db.scalar(stmt)
        if not collection:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="集合不存在")
        return collection

    @staticmethod
    async def get_collections(db: AsyncSession, workspace_id: int):
        """获取工作区中的集合列表"""
        stmt = select(models.WorkspaceCollection).where(models.WorkspaceCollection.workspace_id == workspace_id)
        collections = await db.scalars(stmt)
        return collections.all()

    @staticmethod
    async def create_collection_item(db: AsyncSession, item_data: schemas.WorkspaceCollectionItemCreate):
        """创建集合项"""
        # 检查集合项是否已存在
        stmt = select(models.WorkspaceCollectionItem).where(
            models.WorkspaceCollectionItem.name == item_data.name,
            models.WorkspaceCollectionItem.collection_id == item_data.collection_id
        )
        existing_item = await db.scalar(stmt)
        if existing_item:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="集合项已存在")

        # 创建新集合项
        item = models.WorkspaceCollectionItem(**item_data.dict())
        db.add(item)
        await db.commit()
        await db.refresh(item)
        return item

    @staticmethod
    async def get_collection_items(db: AsyncSession, collection_id: int):
        """获取集合中的所有项"""
        stmt = select(models.WorkspaceCollectionItem).where(
            models.WorkspaceCollectionItem.collection_id == collection_id
        )
        items = await db.scalars(stmt)
        return items.all()
