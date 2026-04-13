from app.schemas.auth import AuthUserRead, LoginRequest, RegisterRequest, TokenResponse
from app.schemas.association import (
    CourseSkillCreate,
    CourseSkillRead,
    CourseSkillUpdate,
    ProfessionSkillCreate,
    ProfessionSkillRead,
    ProfessionSkillUpdate,
    UserCourseCreate,
    UserCourseRead,
    UserCourseUpdate,
    UserProfessionCreate,
    UserProfessionRead,
    UserSkillCreate,
    UserSkillRead,
    UserSkillUpdate,
)
from app.schemas.course import CourseCreate, CourseRead, CourseUpdate
from app.schemas.profession import ProfessionCreate, ProfessionRead, ProfessionUpdate
from app.schemas.skill import SkillCreate, SkillRead, SkillUpdate
from app.schemas.user import UserCreate, UserRead, UserUpdate

__all__ = [
    "UserCreate",
    "UserRead",
    "UserUpdate",
    "SkillCreate",
    "SkillRead",
    "SkillUpdate",
    "CourseCreate",
    "CourseRead",
    "CourseUpdate",
    "ProfessionCreate",
    "ProfessionRead",
    "ProfessionUpdate",
    "UserProfessionCreate",
    "UserProfessionRead",
    "UserSkillCreate",
    "UserSkillRead",
    "UserSkillUpdate",
    "UserCourseCreate",
    "UserCourseRead",
    "UserCourseUpdate",
    "ProfessionSkillCreate",
    "ProfessionSkillRead",
    "ProfessionSkillUpdate",
    "CourseSkillCreate",
    "CourseSkillRead",
    "CourseSkillUpdate",
    "RegisterRequest",
    "LoginRequest",
    "TokenResponse",
    "AuthUserRead",
]
