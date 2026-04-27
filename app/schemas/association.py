from pydantic import BaseModel, ConfigDict, Field

from app.models.skill import SkillLevel


class UserProfessionCreate(BaseModel):
    user_id: int = Field(ge=1)
    profession_id: int = Field(ge=1)


class UserProfessionRead(UserProfessionCreate):
    model_config = ConfigDict(from_attributes=True)


class UserSkillCreate(BaseModel):
    user_id: int = Field(ge=1)
    skill_id: int = Field(ge=1)
    level: SkillLevel = SkillLevel.BEGINNER


class UserSkillUpdate(BaseModel):
    level: SkillLevel


class UserSkillRead(UserSkillCreate):
    model_config = ConfigDict(from_attributes=True)


class UserCourseCreate(BaseModel):
    user_id: int = Field(ge=1)
    course_id: int = Field(ge=1)
    position: int | None = Field(default=None, ge=1)
    is_completed: bool = False


class UserCourseUpdate(BaseModel):
    position: int | None = Field(default=None, ge=1)
    is_completed: bool | None = None


class UserCourseRead(UserCourseCreate):
    model_config = ConfigDict(from_attributes=True)


class ProfessionSkillCreate(BaseModel):
    profession_id: int = Field(ge=1)
    skill_id: int = Field(ge=1)
    weight: int = Field(default=1, ge=0)
    show: bool = True
    display_order: int | None = Field(default=None, ge=0)
    extra: bool = False


class ProfessionSkillUpdate(BaseModel):
    weight: int | None = Field(default=None, ge=0)
    show: bool | None = None
    display_order: int | None = Field(default=None, ge=0)
    extra: bool | None = None


class ProfessionSkillRead(ProfessionSkillCreate):
    model_config = ConfigDict(from_attributes=True)


class CourseSkillCreate(BaseModel):
    course_id: int = Field(ge=1)
    skill_id: int = Field(ge=1)
    from_level: str = Field(min_length=1, max_length=50)
    to_level: str = Field(min_length=1, max_length=50)
    relevance_score: int | None = None


class CourseSkillUpdate(BaseModel):
    from_level: str | None = Field(default=None, min_length=1, max_length=50)
    to_level: str | None = Field(default=None, min_length=1, max_length=50)
    relevance_score: int | None = None


class CourseSkillRead(CourseSkillCreate):
    model_config = ConfigDict(from_attributes=True)
