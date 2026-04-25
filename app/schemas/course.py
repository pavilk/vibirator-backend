from pydantic import BaseModel, ConfigDict, Field, HttpUrl


class CourseBase(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    platform: str = Field(min_length=1, max_length=255)
    url: HttpUrl
    description: str = Field(min_length=1)
    rating: float | None = Field(default=None, ge=0, le=5)
    practices_count: int | None = Field(default=None, ge=0)
    workload_raw: str | None = Field(default=None, max_length=255)
    is_online: bool
    z_e: int | None = Field(default=None, ge=0)
    is_paid: bool | None = None
    target_years: list[int] | None = None
    semesters: list[int] | None = None


class CourseCreate(CourseBase):
    pass


class CourseUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=255)
    platform: str | None = Field(default=None, min_length=1, max_length=255)
    url: HttpUrl | None = None
    description: str | None = Field(default=None, min_length=1)
    rating: float | None = Field(default=None, ge=0, le=5)
    practices_count: int | None = Field(default=None, ge=0)
    workload_raw: str | None = Field(default=None, max_length=255)
    is_online: bool | None = None
    z_e: int | None = Field(default=None, ge=0)
    is_paid: bool | None = None
    target_years: list[int] | None = None
    semesters: list[int] | None = None


class CourseRead(CourseBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
