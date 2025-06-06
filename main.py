import uvicorn

from typing import cast
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, status, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from app.routers import api_router
from core.database import init_db, db_session


@asynccontextmanager
async def lifespan(app_: FastAPI):
    # 初始化数据库
    await init_db()

    # 创建默认权限
    async with db_session() as async_session:
        ...

    yield


app = FastAPI(lifespan=lifespan)


# Customize the return format of Exception
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"message": exc.detail}
    )


# 配置 CORS
origins = [
    "*"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 允许的前端域名
    allow_credentials=True,
    allow_methods=["*"],  # 允许所有方法，如 GET、POST 等
    allow_headers=["*"],  # 允许所有请求头
)

# 注册路由
app.include_router(api_router, prefix="/api/v1")


if __name__ == '__main__':
    uvicorn.run("main:app", host="0.0.0.0", port=8002, reload=True)
