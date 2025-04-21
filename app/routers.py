from fastapi import APIRouter

from .user.router import router as user_router
from .auth.router import router as auth_router
from .collection.router import router as collection_router
from .workspace.router import router as workspace_router


api_router = APIRouter()
api_router.include_router(user_router, prefix="/users", tags=["Users"])
api_router.include_router(auth_router, prefix="/auth", tags=["Auth"])
api_router.include_router(collection_router, prefix="/collections", tags=["Collections"])
api_router.include_router(workspace_router, prefix="/workspaces", tags=["Workspaces"])
