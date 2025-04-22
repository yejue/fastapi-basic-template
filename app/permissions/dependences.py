from typing import Type, Callable, Any, Optional, Dict
from fastapi import Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.user.models import User
from app.auth.dependences import get_current_user
from core.database import get_db
from .engine import PermissionEngine


def require_permission(
        resource_type: str,
        action: str,
        get_resource: Callable,
        context_builder: Optional[Callable] = None
):
    """
    创建一个需要特定权限的依赖

    参数:
        resource_type: 资源类型
        action: 操作名称
        get_resource: 获取资源对象的函数
        context_builder: 构建上下文的函数 (可选)
    """

    async def _check_permission(
            request: Request,
            current_user: User = Depends(get_current_user),
            db: AsyncSession = Depends(get_db),
    ):
        # 获取资源
        resource = await get_resource(db, request=request)

        # 构建上下文
        context = {}
        if context_builder:
            context = context_builder()

        # 创建权限引擎并评估权限
        engine = PermissionEngine(
            db=db,
            user=current_user,
            resource=resource,
            context=context
        )

        if not await engine.evaluate(action):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="权限不足"
            )

        return resource

    return _check_permission
