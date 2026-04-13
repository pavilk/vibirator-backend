from datetime import timedelta

from pydantic import BaseModel, ConfigDict, Field, HttpUrl


class CourseBase(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    platform: str = Field(min_length=1, max_length=255)
    url: HttpUrl
    price: int | None = Field(default=None, ge=0)
    description: str = Field(min_length=1)
    rating: float | None = Field(default=None, ge=0, le=5)
    practices_count: int | None = Field(default=None, ge=0)
    duration: timedelta | None = None
    is_online: bool
    z_e: int | None = Field(default=None, ge=0)
    semester: int | None = Field(default=None, ge=1)


class CourseCreate(CourseBase):
    pass


class CourseUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=255)
    platform: str | None = Field(default=None, min_length=1, max_length=255)
    url: HttpUrl | None = None
    price: int | None = Field(default=None, ge=0)
    description: str | None = Field(default=None, min_length=1)
    rating: float | None = Field(default=None, ge=0, le=5)
    practices_count: int | None = Field(default=None, ge=0)
    duration: timedelta | None = None
    is_online: bool | None = None
    z_e: int | None = Field(default=None, ge=0)
    semester: int | None = Field(default=None, ge=1)


class CourseRead(CourseBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
