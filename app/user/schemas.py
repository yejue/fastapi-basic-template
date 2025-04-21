from pydantic import BaseModel, Field


class UserBaseSchema(BaseModel):
    username: str = Field(description="用户名")


class UserCreate(UserBaseSchema):
    is_superuser: bool = Field(False, description="超级用户")
    password: str = Field(description="密码")


class UserResponse(UserBaseSchema):
    id: int = Field(description="用户ID")
    is_superuser: bool = Field(description="是否超级用户")
    is_active: bool = Field(description="是否可用")

    class Config:
        from_attributes = True
