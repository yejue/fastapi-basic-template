from typing import Optional, Any, Generic, TypeVar, Type

from pydantic import BaseModel, model_validator, Field

from fastapi import status
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder


T = TypeVar("T")


class ResponseBase(BaseModel, Generic[T]):
    message: Optional[str] = "OK"
    data: Optional[T] = None
    total: Optional[int] = None
    page: Optional[int] = None
    size: Optional[int] = None

    @classmethod
    @model_validator(mode="before")
    def auto_fill_pagination(cls, data: Any) -> dict:
        """自动填充分页字段并处理不同数据类型"""
        if not isinstance(data, dict):
            raw_data = data
            data = {"data": raw_data}  # 统一为字典处理
        else:
            raw_data = data.get("data")

        # 分页对象处理（例如 fastapi-paginate 的 Page 对象）
        if hasattr(raw_data, "total") and hasattr(raw_data, "items"):
            data["data"] = jsonable_encoder(raw_data.items)
            data["total"] = raw_data.total
            data["page"] = raw_data.page
            data["size"] = raw_data.size

        # 普通列表处理（自动计算总数）
        elif isinstance(raw_data, list):
            data["data"] = jsonable_encoder(raw_data)

        # SQLAlchemy ORM 对象处理
        elif hasattr(raw_data, "__table__"):
            data["data"] = jsonable_encoder(raw_data)

        # 其他类型直接序列化
        else:
            data["data"] = jsonable_encoder(raw_data)
        return data


def resp_(data_model: Type[T]) -> Type[ResponseBase[T]]:
    class ConcreteResponse(ResponseBase[data_model]):  # type: ignore
        pass
    return ConcreteResponse


async def json_response(
    status_code: int = status.HTTP_200_OK,
    message: Optional[str] = None,
    data: Optional[Any] = None,
    total: Optional[int] = None,
    page: Optional[int] = None,
    size: Optional[int] = None,
    **kwargs
) -> JSONResponse:

    content = {
        "message": message,
        "data": data,
        "total": total,
        "page": page,
        "size": size
    }

    if kwargs:
        content.update(kwargs)

    return JSONResponse(status_code=status_code, content=content)
