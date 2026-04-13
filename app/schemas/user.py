from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserBase(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    email: EmailStr
    semester: int | None = Field(default=None, ge=1)


class UserCreate(UserBase):
    password: str = Field(min_length=8, max_length=255)


class UserUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    email: EmailStr | None = None
    password: str | None = Field(default=None, min_length=8, max_length=255)
    semester: int | None = Field(default=None, ge=1)


class UserRead(UserBase):
    model_config = ConfigDict(from_attributes=True)

    user_id: int
    is_admin: bool
