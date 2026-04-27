from pydantic import BaseModel, ConfigDict, HttpUrl


class ScoredCourseRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    platform: str
    url: HttpUrl
    description: str
    rating: float | None = None
    practices_count: int | None = None
    workload_raw: str | None = None
    is_online: bool
    z_e: int | None = None
    is_paid: bool | None = None
    target_years: list[int] | None = None
    semesters: list[int] | None = None
    skill_id: int
    score: float


class SkillRecommendation(BaseModel):
    skill_id: int
    skill_name: str
    user_level: str
    recommended_course: ScoredCourseRead | None = None


class SkillCoursesResponse(BaseModel):
    skill_id: int
    skill_name: str
    user_level: str
    urfu_courses: list[ScoredCourseRead] | None = None
    other_courses: list[ScoredCourseRead]


class RecommendationResponse(BaseModel):
    user_id: int
    profession_id: int
    recommendations: list[SkillRecommendation]
