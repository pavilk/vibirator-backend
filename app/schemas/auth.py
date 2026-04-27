from pydantic import BaseModel, ConfigDict, EmailStr, Field


class RegisterRequest(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    email: EmailStr
    password: str = Field(min_length=8, max_length=255)
    semester: int | None = Field(default=None, ge=1)
    is_fiit: bool = False
    course_year: int | None = Field(default=None, ge=1, le=6)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class AuthUserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    user_id: int
    name: str
    email: EmailStr
    semester: int | None = None
    is_admin: bool
    is_fiit: bool
    course_year: int | None = None
