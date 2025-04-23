from typing import List

from fastapi import APIRouter, Depends

from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependences import get_current_user, get_current_superuser

from core.database import get_db
from . import schemas, services

router = APIRouter()


@router.post("", response_model=schemas.CollectionResponse)
async def create_collection(
    collection: schemas.CollectionCreate,
    current=Depends(get_current_superuser),
    db: AsyncSession = Depends(get_db),
):
    """创建集合"""
    return await services.CollectionService.create_collection(db, collection)


@router.get("", response_model=List[schemas.CollectionResponse])
async def get_collections(
    current_user=Depends(get_current_superuser),
    db: AsyncSession = Depends(get_db),
):
    """获取集合列表"""
    return await services.CollectionService.get_collections(db)


@router.get("/{collection_id}", response_model=schemas.CollectionResponse)
async def get_collection(
    collection_id: int,
    current=Depends(get_current_superuser),
    db: AsyncSession = Depends(get_db)
):
    """获取集合详情"""
    return await services.CollectionService.get_collection_by_id(db, collection_id)


@router.post("/{collection_id}/items", response_model=schemas.CollectionItemResponse)
async def create_collection_item(
    collection_id: int,
    item: schemas.CollectionItemCreate,
    current=Depends(get_current_superuser),
    db: AsyncSession = Depends(get_db)
):
    """创建集合项"""
    item.collection_id = collection_id
    return await services.CollectionService.create_collection_item(db, item)


@router.get("/{collection_id}/items", response_model=List[schemas.CollectionItemResponse])
async def get_collection_items(
    collection_id: int,
    current=Depends(get_current_superuser),
    db: AsyncSession = Depends(get_db)
):
    """获取集合中的所有项"""
    return await services.CollectionService.get_collection_items(db, collection_id)
