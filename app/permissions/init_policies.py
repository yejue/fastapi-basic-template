from pathlib import Path
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from .models import AbacPolicy, Permission
from app.workspace.models import Workspace, WorkspaceRole


async def create_default_permissions(db: AsyncSession):
    """创建默认的权限"""

    # 检查是否已存在权限
    result = await db.execute(select(Permission))
    if result.scalars().first():
        return

    # 创建默认权限
    default_permissions = [
        Permission(name="workspace.read", description="读取工作区"),
        Permission(name="workspace.create", description="创建工作区"),
        Permission(name="workspace.update", description="更新工作区"),
        Permission(name="workspace.delete", description="删除工作区"),
        Permission(name="workspace.invite", description="邀请用户加入工作区"),
        Permission(name="collection.read", description="读取集合"),
        Permission(name="collection.create", description="创建集合"),
        Permission(name="collection.update", description="更新集合"),
        Permission(name="collection.delete", description="删除集合"),
        Permission(name="item.read", description="读取项目"),
        Permission(name="item.create", description="创建项目"),
        Permission(name="item.update", description="更新项目"),
        Permission(name="item.delete", description="删除项目"),
    ]

    for permission in default_permissions:
        db.add(permission)

    await db.commit()

    # 分配权限到角色
    await assign_permissions_to_roles(db)


async def assign_permissions_to_roles(db: AsyncSession):
    """分配权限到默认角色"""

    # 获取所有权限
    result = await db.execute(select(Permission))
    permissions = {p.name: p for p in result.scalars().all()}

    # 获取所有角色
    result = await db.execute(select(WorkspaceRole))
    roles = result.scalars().all()

    for role in roles:
        if role.name == "administrator":
            # 管理员拥有所有权限
            role.permissions.extend(list(permissions.values()))
        # elif role.name == "engineer":
        #     # 工程师拥有除了删除外的所有权限
        #     engineer_permissions = [
        #         permissions["workspace.read"],
        #         permissions["workspace.update"],
        #         permissions["collection.read"],
        #         permissions["collection.create"],
        #         permissions["collection.update"],
        #         permissions["item.read"],
        #         permissions["item.create"],
        #         permissions["item.update"],
        #     ]
        #     role.permissions.extend(engineer_permissions)
        # elif role.name == "labeler":
        #     # 标注员只有读取和更新项目的权限
        #     annotator_permissions = [
        #         permissions["workspace.read"],
        #         permissions["collection.read"],
        #         permissions["item.read"],
        #         permissions["item.update"],
        #     ]
        #     role.permissions.extend(annotator_permissions)

    await db.commit()


async def create_default_policies(db: AsyncSession):
    """创建默认的 ABAC 策略"""

    # 创建默认权限
    await create_default_permissions(db)

    # 检查是否已存在策略
    # result = await db.execute(select(AbacPolicy))
    # if result.scalars().first():
    #     return
    #
    # # 创建默认策略
    # default_policies = [
    #     # 标注员只能在工作日访问资源
    #     AbacPolicy(
    #         name="标注员工作日访问",
    #         resource_type="workspace",
    #         action="read",
    #         condition={
    #             "user.workspace_users[0].role.name": "== 'labeler'",
    #             "context.weekday": "in [0,1,2,3,4]"
    #         }
    #     ),
    #     # 工程师可以随时访问资源
    #     AbacPolicy(
    #         name="工程师访问",
    #         resource_type="workspace",
    #         action="read",
    #         condition={
    #             "user.workspace_users[0].role.name": "== 'engineer'"
    #         }
    #     ),
    # ]
    #
    # for policy in default_policies:
    #     db.add(policy)

    # await db.commit()
